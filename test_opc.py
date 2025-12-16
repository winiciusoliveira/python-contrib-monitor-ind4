import asyncio
from asyncua import Client
import logging

# Habilita log detalhado da biblioteca (Mostra handshake, pacotes, tudo)
logging.basicConfig(level=logging.WARNING)

# --- CONFIGURE AQUI PARA TESTAR ---
ENDPOINT = "opc.tcp://10.243.67.14:4870"  # IP do Tear#01
NODE_ID = "ns=3;s=machine running"  # NodeID do Tear#01

# ----------------------------------

async def debug_opc() :
	print(f"🔌 Tentando conectar em: {ENDPOINT}")
	print(f"🎯 Buscando NodeID: {NODE_ID}")
	
	client = Client(url=ENDPOINT)
	try :
		async with client :
			print("✅ Conexão TCP/OPC estabelecida!")
			
			# 1. Tenta pegar o Namespace Array (Diagnóstico básico)
			ns_idx = await client.get_namespace_array()
			print(f"📂 Namespaces disponíveis: {len(ns_idx)}")
			
			# 2. Tenta pegar o nó específico
			node = client.get_node(NODE_ID)
			print(f"✅ Nó encontrado objeto: {node}")
			
			# 3. Tenta ler o valor
			val = await node.read_value()
			print(f"📊 LEITURA SUCESSO! Valor: {val} (Tipo: {type(val)})")
	
	except Exception as e :
		print("\n❌ FALHA NO TESTE:")
		print(f"Erro: {e}")
		print("-" * 30)
		print("Dicas:")
		print("1. Se o erro for 'BadNodeIdUnknown': O NodeID 's=...' está errado. Verifique aspas e espaços.")
		print("2. Se o erro for 'Timeout': O firewall liberou a porta 4840 mas bloqueou o pacote OPC.")
		print("3. Se o erro for 'BadIdentityTokenRejected': O PLC pede usuário/senha.")

if __name__ == "__main__" :
	asyncio.run(debug_opc())
