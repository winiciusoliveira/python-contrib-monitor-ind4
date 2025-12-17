import socket
import subprocess
import platform
import concurrent.futures

def check_ping(ip) :
	# Define parâmetros baseados no sistema operacional
	param = '-n' if platform.system().lower() == 'windows' else '-c'
	# Timeout curto (1000ms) para agilidade
	command = ['ping', param, '1', '-w', '1000', ip] if platform.system().lower() == 'windows' else ['ping', '-c', '1', '-W', '1', ip]
	
	try :
		return subprocess.call(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0
	except :
		return False

def check_port(ip, port) :
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.settimeout(1.0)  # Timeout de 1 segundo
	try :
		result = s.connect_ex((ip, int(port)))
		s.close()
		return result == 0
	except :
		return False

def _check_single_machine(machine) :
	"""Worker que testa uma única máquina."""
	status_host = check_ping(machine['ip'])
	
	if status_host :
		# Só testa porta se o host respondeu ao ping
		status_service = check_port(machine['ip'], machine['porta'])
		if status_service :
			estado = "🟢 ONLINE"
		else :
			estado = "⚠️ FALHA OPC"
	else :
		estado = "🔴 SEM CONEXÃO"
	
	return {
		"Máquina" : machine['nome'], "IP" : machine['ip'], "Status" : estado
	}

def scan_machines(lista_maquinas) :
	"""Executa o scan em paralelo (multithreading)."""
	results = []
	# 30 workers garante que todas as máquinas sejam testadas simultaneamente
	with concurrent.futures.ThreadPoolExecutor(max_workers=30) as executor :
		future_to_machine = { executor.submit(_check_single_machine, m) : m for m in lista_maquinas }
		for future in concurrent.futures.as_completed(future_to_machine) :
			results.append(future.result())
	return results
