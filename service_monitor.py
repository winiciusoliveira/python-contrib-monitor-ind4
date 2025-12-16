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
import opc_config

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
	# Armazena o datetime de QUANDO parou: {'Tear#01': datetime_obj}
	inicio_paradas = { }
	# Controle de estabilidade para retorno (Histerese)
	estabilidade_recuperacao = { }
	
	primeira_execucao = True
	
	while True :
		inicio_scan = time.time()
		maquinas = carregar_maquinas()
		print(f"🔍 Scan: {len(maquinas)} máquinas...", end=" ")
		
		# Coletas
		dados_rede = network_utils.scan_machines(maquinas)
		dados_api = integration_api.fetch_metris_status()
		mapa_resultados_opc = opc_utils.check_opc_batch(maquinas, opc_config.OPC_MAP)
		
		houve_mudanca = False
		timestamp_agora = datetime.now()  # Objeto datetime para cálculos
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
				status_detectado = "🔴 SEM REDE"
				cor_final = "#dc3545"
			elif "FALHA OPC" in status_infra :
				status_detectado = "⚠️ FALHA PORTA OPC"
				cor_final = "#ffc107"
			elif opc_real_value is True :
				# Se está rodando
				if "AGUARDANDO" in status_api_desc or "Unknown" in status_api_desc :
					status_detectado = "🟢 PRODUZINDO"
				else :
					status_detectado = f"🟢 PRODUZINDO | {status_api_desc}"
				cor_final = "#28a745"
			elif opc_real_value is False :
				status_detectado = f"⏹️ PARADA | {status_api_desc}"
			elif opc_real_value is None :
				status_detectado = "⚠️ ERRO LEITURA TAG"
				cor_final = "#fd7e14"
			
			# --- PROCESSAMENTO DE ESTADO ---
			memoria = estado_persistente.get(nome_config, { })
			status_anterior = memoria.get('status', 'DESCONHECIDO')
			contador = memoria.get('contador', 0)
			
			# Novo contador de falha de rede
			novo_contador = contador + 1 if "SEM REDE" in status_detectado else 0
			status_para_salvar = status_detectado
			
			# 1. Debounce de Rede
			if "SEM REDE" in status_detectado and novo_contador < LIMITE_FALHAS :
				status_para_salvar = status_anterior
			
			# 2. Histerese de Retorno (Só confirma PRODUZINDO após TEMPO_ESTABILIDADE)
			elif "PRODUZINDO" in status_detectado and "PRODUZINDO" not in status_anterior :
				if nome_config not in estabilidade_recuperacao :
					estabilidade_recuperacao[nome_config] = time.time()
				
				if (time.time() - estabilidade_recuperacao[nome_config]) < TEMPO_ESTABILIDADE :
					status_para_salvar = status_anterior  # Segura o status antigo
				else :
					# CONFIRMOU QUE VOLTOU! HORA DE FECHAR O CICLO DE PARADA
					status_para_salvar = status_detectado
					estabilidade_recuperacao.pop(nome_config, None)
					
					# Se estava em parada, calcula e salva no banco
					if nome_config in inicio_paradas :
						dt_inicio = inicio_paradas.pop(nome_config)
						dt_fim = timestamp_agora
						
						# Salva no Banco SQL (Novo Schema)
						mins, tempo_fmt, motivo_limpo = database.salvar_ciclo_parada(nome_config, planta, setor, dt_inicio, dt_fim, status_anterior)
						
						# Dispara Notificação Filtrada
						msg = f"✅ **{nome_config} Voltou**\n" \
						      f"🕒 Ficou parado: {tempo_fmt} ({mins} min)\n" \
						      f"🔧 Motivo: {motivo_limpo}"
						
						notifications.enviar_notificacao_inteligente(msg, motivo_limpo, mins)
			
			# 3. Lógica de Parada (Registra início imediatamente)
			elif "PRODUZINDO" not in status_detectado :
				if nome_config in estabilidade_recuperacao :
					estabilidade_recuperacao.pop(nome_config, None)
				
				# Se não estava parado antes, marca o início
				if "PRODUZINDO" in status_anterior and nome_config not in inicio_paradas :
					inicio_paradas[
						nome_config] = timestamp_agora  # Opcional: Avisar no Teams imediatamente que parou?   # Se quiser avisar "Parou" na hora, descomente:  # notifications.enviar_notificacao_inteligente(f"🛑 {nome_config} PAROU: {status_detectado}", "PARADA", 0)
				
				status_para_salvar = status_detectado
			
			# Salva mudanças para o Dashboard (Tempo Real)
			if status_para_salvar != status_anterior :
				houve_mudanca = True
				# Registra evento bruto para debug
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
		
		# Inicialização e Watchdog
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