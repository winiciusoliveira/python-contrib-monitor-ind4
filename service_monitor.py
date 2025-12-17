import time
from datetime import datetime
import json
import os

# Módulos locais
import database
import network_utils
import notifications
import integration_api
import opc_utils

# REMOVIDO: import opc_config (Não usamos mais, dados vêm do config.json)

# --- CONFIGURAÇÃO ---
LIMITE_FALHAS = 3
INTERVALO_SCAN = 5
TEMPO_ESTABILIDADE = 60  # Para confirmar que VOLTOU a produzir

def carregar_maquinas() :
	try :
		with open('config.json', 'r', encoding='utf-8') as f :
			return json.load(f)
	except :
		return []

def salvar_dados_completos(estado_maquinas) :
	dados = {
		"metadata" : {
			"ultimo_sinal" : datetime.now().strftime('%Y-%m-%d %H:%M:%S'), "status_servico" : "RODANDO", "versao_python" : "3.12.10 (Smart Database)"
		}, "maquinas" : estado_maquinas
	}
	database.salvar_estado_persistente(dados)

def loop_principal() :
	print(f"🚀 Serviço Monitoramento (DB + Filtros) - {datetime.now()}")
	database.init_db()
	
	json_completo = database.carregar_estado_persistente()
	estado_persistente = json_completo.get("maquinas", { }) if "maquinas" in json_completo else json_completo
	
	# Dicionários de controle
	inicio_paradas = { }
	estabilidade_recuperacao = { }
	
	primeira_execucao = True
	
	while True :
		inicio_scan = time.time()
		maquinas = carregar_maquinas()
		print(f"🔍 Scan: {len(maquinas)} máquinas...", end=" ")
		
		# --- CORREÇÃO: GERAÇÃO DINÂMICA DO MAPA OPC ---
		# Extrai os dados OPC do config.json, eliminando a dependência do arquivo opc_config.py
		opc_map_config = { }
		for m in maquinas :
			if "opc_config" in m and "api_id" in m :
				opc_map_config[m["api_id"]] = m["opc_config"]
		# -----------------------------------------------
		
		# Coletas
		dados_rede = network_utils.scan_machines(maquinas)
		dados_api = integration_api.fetch_metris_status()
		mapa_resultados_opc = opc_utils.check_opc_batch(maquinas, opc_map_config)
		
		houve_mudanca = False
		timestamp_agora = datetime.now()
		str_agora = timestamp_agora.strftime('%Y-%m-%d %H:%M:%S')
		
		for item_rede in dados_rede :
			nome_config = item_rede['Máquina']
			ip_maquina = item_rede['IP']
			status_infra = item_rede['Status']
			
			maq_config = next((m for m in maquinas if m['nome'] == nome_config), None)
			api_id = maq_config.get('api_id', '') if maq_config else ''
			
			# Dados API e Config
			info_api = dados_api.get(api_id, { })
			status_api_desc = info_api.get('descricao', 'DESCONHECIDO')
			cor_api = info_api.get('cor', '#808080')
			unidade = maq_config.get('unidade', 'Geral')
			planta = maq_config.get('planta', 'Geral')
			setor = maq_config.get('setor', 'Geral')
			
			# Leitura OPC
			opc_real_value = None
			if "ONLINE" in status_infra or "FALHA OPC" not in status_infra :
				opc_real_value = mapa_resultados_opc.get(api_id, None)
			
			# --- DECISÃO DE STATUS ---
			status_detectado = status_api_desc
			cor_final = cor_api
			
			if "SEM CONEXÃO" in status_infra :
				status_detectado = "SEM REDE"
				cor_final = "#dc3545"
			elif "FALHA OPC" in status_infra :
				status_detectado = "⚠️ FALHA PORTA OPC"
				cor_final = "#ffc107"
			elif opc_real_value is True :
				if "AGUARDANDO" in status_api_desc or "Unknown" in status_api_desc :
					status_detectado = "PRODUZINDO"
				else :
					status_detectado = f"PRODUZINDO | {status_api_desc}"
				cor_final = "#28a745"
			elif opc_real_value is False :
				status_detectado = f"PARADA | {status_api_desc}"
			elif opc_real_value is None :
				status_detectado = "⚠️ ERRO LEITURA TAG"
				cor_final = "#fd7e14"
			
			# --- PROCESSAMENTO DE ESTADO ---
			memoria = estado_persistente.get(nome_config, { })
			status_anterior = memoria.get('status', 'DESCONHECIDO')
			contador = memoria.get('contador', 0)
			
			novo_contador = contador + 1 if "SEM REDE" in status_detectado else 0
			status_para_salvar = status_detectado
			
			if "SEM REDE" in status_detectado and novo_contador < LIMITE_FALHAS :
				status_para_salvar = status_anterior
			
			elif "PRODUZINDO" in status_detectado and "PRODUZINDO" not in status_anterior :
				if nome_config not in estabilidade_recuperacao :
					estabilidade_recuperacao[nome_config] = time.time()
				
				if (time.time() - estabilidade_recuperacao[nome_config]) < TEMPO_ESTABILIDADE :
					status_para_salvar = status_anterior
				else :
					status_para_salvar = status_detectado
					estabilidade_recuperacao.pop(nome_config, None)
					
					if nome_config in inicio_paradas :
						dt_inicio = inicio_paradas.pop(nome_config)
						dt_fim = timestamp_agora
						
						mins, tempo_fmt, motivo_limpo = database.salvar_ciclo_parada(nome_config, planta, setor, dt_inicio, dt_fim, status_anterior)
						
						msg = f"✅ **{nome_config} Voltou**\n" \
						      f"🕒 Ficou parado: {tempo_fmt} ({mins} min)\n" \
						      f"🔧 Motivo: {motivo_limpo}"
						
						notifications.enviar_notificacao_inteligente(msg, motivo_limpo, mins)
			
			elif "PRODUZINDO" not in status_detectado :
				if nome_config in estabilidade_recuperacao :
					estabilidade_recuperacao.pop(nome_config, None)
				
				if "PRODUZINDO" in status_anterior and nome_config not in inicio_paradas :
					inicio_paradas[nome_config] = timestamp_agora
				
				status_para_salvar = status_detectado
			
			if status_para_salvar != status_anterior :
				houve_mudanca = True
				database.registrar_evento(nome_config, status_anterior, status_para_salvar)
			
			estado_persistente[nome_config] = {
				'status' : status_para_salvar,
				'cor' : cor_final,
				'desde' : str_agora if status_para_salvar != status_anterior else memoria.get('desde', str_agora),
				'contador' : novo_contador,
				'ip' : ip_maquina,
				'unidade' : unidade,
				'planta' : planta,
				'setor' : setor
			}
		
		if primeira_execucao :
			notifications.enviar_notificacao_inteligente("🚀 Sistema Reiniciado (Nova Lógica DB)", "SISTEMA", 0)
			primeira_execucao = False
			salvar_dados_completos(estado_persistente)
		
		if houve_mudanca or (time.time() - globals().get('last_save', 0) > 30) :
			salvar_dados_completos(estado_persistente)
			globals()['last_save'] = time.time()
			if houve_mudanca : print("💾 JSON Atualizado.")
		
		tempo_gasto = time.time() - inicio_scan
		print(f"⏱️ {tempo_gasto:.2f}s")
		time.sleep(max(0.0, INTERVALO_SCAN - tempo_gasto))

if __name__ == "__main__" :
	loop_principal()