import subprocess
import sys
import time
import os
import signal

def main() :
	print("🚀 Inicializando Sistema de Monitoramento Industrial...")
	
	# Define os caminhos (garante que use o mesmo Python do ambiente atual)
	python_exe = sys.executable
	
	# 1. Inicia o BACKEND (Service Monitor)
	print("⚙️  Iniciando Backend (service_monitor.py)...")
	processo_monitor = subprocess.Popen([python_exe, "service_monitor.py"], cwd=os.getcwd(), shell=True  # Abre em nova janela/processo dependendo do OS
	                                    )
	
	# Aguarda um pouco para o backend criar o DB e o JSON
	time.sleep(3)
	
	# 2. Inicia o FRONTEND (Streamlit Dashboard)
	print("📊 Iniciando Frontend (dashboard.py)...")
	# Usamos "python -m streamlit" para garantir que pegue o streamlit correto
	processo_dashboard = subprocess.Popen([python_exe, "-m", "streamlit", "run", "dashboard.py"], cwd=os.getcwd(), shell=True)
	
	print("\n✅ Sistema Operacional.")
	print("Pressione Ctrl+C neste terminal para encerrar TODO o sistema.\n")
	
	try :
		# Mantém o script rodando enquanto os filhos existirem
		while True :
			time.sleep(1)
			# Verifica se algum processo morreu inesperadamente
			if processo_monitor.poll() is not None :
				print("❌ ERRO CRÍTICO: O Service Monitor parou inesperadamente!")
				break
			if processo_dashboard.poll() is not None :
				print("⚠️ Aviso: O Dashboard foi fechado.")
				break
	
	except KeyboardInterrupt :
		print("\n🛑 Encerrando sistema...")
	
	finally :
		# Garante que todos os processos sejam mortos ao sair
		print("Finalizando processos filhos...")
		
		# Tenta matar de forma graciosa, se não força
		try :
			# No Windows, kill() é necessário muitas vezes para subprocessos shell
			if platform.system() == "Windows" :
				subprocess.call(['taskkill', '/F', '/T', '/PID', str(processo_monitor.pid)])
				subprocess.call(['taskkill', '/F', '/T', '/PID', str(processo_dashboard.pid)])
			else :
				processo_monitor.terminate()
				processo_dashboard.terminate()
		except :
			pass
		
		print("Tchau! 👋")

if __name__ == "__main__" :
	import platform  # Importação tardia apenas para checagem do OS no finally
	
	main()
