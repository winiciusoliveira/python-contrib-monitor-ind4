import asyncio
from asyncua import Client

# --- NOTA DE MANUTENÇÃO ---
# Este módulo usa a biblioteca 'asyncua' que é nativamente assíncrona.
# Diferente de threads, ela usa um único núcleo do processador mas gerencia
# conexões de rede (I/O) de forma muito eficiente esperando respostas.
# --------------------------

async def _ler_tag_individual(api_id, config_entry) :
	"""
	Worker: Tenta conectar e ler UMA única máquina.
	Retorna uma tupla: (api_id, valor_lido)
	"""
	endpoint = config_entry['endpoint']
	node_id = config_entry['node_running']
	
	# Configuração do Cliente OPC
	client = Client(url=endpoint)
	
	# --- TIMEOUTS ROBUSTOS ---
	# Valores em milissegundos (30s para handshake lento de CLPs antigos)
	client.session_timeout = 30000
	client.secure_channel_timeout = 30000
	client.timeout = 10  # 10s para conexão TCP pura
	
	try :
		# Tenta conectar (await libera o processador para outras tarefas enquanto espera)
		await client.connect()
		
		try :
			node = client.get_node(node_id)
			# Lê o valor booleano (True/False)
			val = await node.read_value()
			return (api_id, val)
		
		finally :
			# Garante que a conexão feche mesmo se der erro na leitura
			try :
				await client.disconnect()
			except :
				pass
	
	except asyncio.TimeoutError :
		# Se estourar o tempo limite
		# print(f"⏱️ Timeout: {api_id}") # Descomente para debug detalhado
		return (api_id, None)
	
	except Exception :
		# Qualquer outro erro (recusado, rede, etc)
		# print(f"❌ Erro: {api_id}") # Descomente para debug detalhado
		return (api_id, None)

async def _orquestrador_scan(lista_para_escanear) :
	"""
	Cria uma lista de tarefas (Tasks) e dispara todas ao mesmo tempo.
	"""
	tarefas = []
	
	# 1. Prepara as "promessas" de execução
	for api_id, config in lista_para_escanear.items() :
		# Cria a tarefa mas não espera ela terminar ainda
		tarefa = _ler_tag_individual(api_id, config)
		tarefas.append(tarefa)
	
	# 2. Dispara todas e aguarda o retorno agrupado (Scatter-Gather)
	# return_exceptions=True impede que o erro de uma máquina pare as outras
	resultados = await asyncio.gather(*tarefas, return_exceptions=True)
	
	return resultados

def check_opc_batch(maquinas_config, opc_map_config) :
	"""
	FUNÇÃO PRINCIPAL (Síncrona) chamada pelo service_monitor.

	1. Filtra quais máquinas do config.json têm configuração OPC.
	2. Inicia o Loop de Eventos do Python.
	3. Retorna um Dicionário: {'LOOM01': True, 'LOOM02': False, ...}
	"""
	# Filtra apenas máquinas que existem no opc_config.py
	lista_opc = { }
	for maq in maquinas_config :
		aid = maq.get('api_id')
		if aid in opc_map_config :
			lista_opc[aid] = opc_map_config[aid]
	
	if not lista_opc :
		return { }
	
	# --- MÁGICA DO PARALELISMO ---
	# asyncio.run cria o loop, roda tudo e fecha o loop.
	# Isso substitui o "for" lento do arquivo antigo.
	lista_tuplas = asyncio.run(_orquestrador_scan(lista_opc))
	
	# Converte lista de tuplas [('LOOM01', True), ...] em Dicionário {'LOOM01': True}
	resultado_final = { }
	for item in lista_tuplas :
		if isinstance(item, tuple) and len(item) == 2 :
			key, val = item
			resultado_final[key] = val
	
	return resultado_final