import requests

API_URL = "http://10.243.67.248:3000/proxy/integracao-metris/v1/classificacao-maquina?codigoRecurso=all&fake=false&estabelecimento=1&setor=tecelagem"

def fetch_metris_status() :
	"""
	Busca o status de produção da API Metris.
	Retorna um Dicionário indexado pelo nome do recurso para busca rápida.
	Ex: {'LOOM01': {'descricao': 'MÁQUINA OPERANDO', 'cor': '#007B38'}}
	"""
	try :
		response = requests.get(API_URL, timeout=3)
		if response.status_code == 200 :
			dados_raw = response.json()
			mapa_status = { }
			
			for item in dados_raw :
				recurso = item.get('recurso', '').upper()
				
				# Tratamento de Cor (A API manda FF007B38, precisamos de #007B38)
				cor_raw = item.get('corStatus', 'FF808080')  # Cinza padrão se falhar
				cor_hex = f"#{cor_raw[2 :]}" if len(cor_raw) == 8 else "#808080"
				
				descricao = item.get('descricao', 'AGUARDANDO CLASSIFICAÇÃO')
				if item.get('aguardandoClassificacao') :
					descricao = "AGUARDANDO CLASSIFICAÇÃO"
				
				mapa_status[recurso] = {
					"descricao" : descricao, "codigo" : item.get('codigo', 0), "status_bin" : item.get('status', 0),  # 1=Rodando, 0=Parado
					"cor" : cor_hex
				}
			return mapa_status
	except Exception as e :
		print(f"⚠️ Erro ao consultar API Metris: {e}")
	
	return { }  # Retorna vazio em caso de erro, para não quebrar o sistema
