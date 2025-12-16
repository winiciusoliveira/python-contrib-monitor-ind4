import sqlite3
import pandas as pd
from datetime import datetime, time
import json
import os
import uuid

DB_NAME = "monitoramento.db"
STATE_FILE = "estado_atual.json"

def init_db() :
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	# Tabela Histórica Completa (Ciclos Fechados)
	cursor.execute('''
                   CREATE TABLE IF NOT EXISTS historico_paradas
                   (
                       uuid
                       TEXT
                       PRIMARY
                       KEY,
                       equipamento
                       TEXT,
                       planta
                       TEXT,
                       setor
                       TEXT,
                       data_inicial
                       TEXT,
                       data_final
                       TEXT,
                       minutos_parado
                       REAL,
                       tempo_formatado
                       TEXT,
                       motivo
                       TEXT,
                       turno
                       TEXT
                   )
	               ''')
	# Tabela de Eventos (Log Bruto - Opcional manter ou não)
	cursor.execute('''
                   CREATE TABLE IF NOT EXISTS eventos
                   (
                       id
                       INTEGER
                       PRIMARY
                       KEY
                       AUTOINCREMENT,
                       timestamp
                       TEXT,
                       maquina
                       TEXT,
                       status_anterior
                       TEXT,
                       status_novo
                       TEXT
                   )
	               ''')
	conn.commit()
	conn.close()

def calcular_turno(dt_obj) :
	"""
	Define o turno com base no horário de Piracicaba.
	T1: 06:00 - 14:30 | T2: 14:30 - 22:52 | T3: 22:52 - 06:00
	"""
	t = dt_obj.time()
	# Converte tudo para minutos do dia para facilitar comparação
	minutos = t.hour * 60 + t.minute
	
	t1_start = 6 * 60  # 06:00
	t2_start = 14 * 60 + 30  # 14:30
	t3_start = 22 * 60 + 52  # 22:52
	
	if t1_start <= minutos < t2_start :
		return "TURNO 01"
	elif t2_start <= minutos < t3_start :
		return "TURNO 02"
	else :
		return "TURNO 03"  # Cobre o final da noite e madrugada

def formatar_duracao(segundos) :
	"""Formata segundos em dd-hh:mm:ss"""
	m, s = divmod(segundos, 60)
	h, m = divmod(m, 60)
	d, h = divmod(h, 24)
	if d > 0 :
		return f"{int(d):02d}-{int(h):02d}:{int(m):02d}:{int(s):02d}"
	return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

def salvar_ciclo_parada(maquina, planta, setor, dt_inicio, dt_fim, motivo) :
	"""Salva o registro completo quando a máquina VOLTA a rodar"""
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	
	# Cálculos
	duracao = (dt_fim - dt_inicio).total_seconds()
	minutos = round(duracao / 60, 2)
	tempo_fmt = formatar_duracao(duracao)
	
	# Limpeza do Motivo (Upper case e sem emojis básicos - expandir regex se precisar)
	motivo_limpo = motivo.encode('ascii', 'ignore').decode('ascii').strip().upper()
	if not motivo_limpo : motivo_limpo = motivo.upper()  # Fallback se o encode remover tudo
	
	turno = calcular_turno(dt_inicio)
	id_unico = str(uuid.uuid4())
	
	cursor.execute('''
                   INSERT INTO historico_paradas
                       (uuid, equipamento, planta, setor, data_inicial, data_final, minutos_parado, tempo_formatado, motivo, turno)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
	               ''', (id_unico, maquina, planta, setor, str(dt_inicio), str(dt_fim), minutos, tempo_fmt, motivo_limpo, turno))
	
	conn.commit()
	conn.close()
	return minutos, tempo_fmt, motivo_limpo  # Retorna para usar na notificação

# --- Funções Mantidas ---
def registrar_evento(maquina, status_ant, status_novo) :
	conn = sqlite3.connect(DB_NAME)
	cursor = conn.cursor()
	timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
	cursor.execute('INSERT INTO eventos (timestamp, maquina, status_anterior, status_novo) VALUES (?, ?, ?, ?)', (timestamp, maquina, status_ant, status_novo))
	conn.commit()
	conn.close()

def carregar_estado_persistente() :
	if not os.path.exists(STATE_FILE) : return { }
	try :
		with open(STATE_FILE, 'r', encoding='utf-8') as f :
			return json.load(f)
	except :
		return { }

def salvar_estado_persistente(dados) :
	try :
		with open(STATE_FILE, 'w', encoding='utf-8') as f :
			json.dump(dados, f, indent=4)
	except Exception as e :
		print(f"Erro ao salvar: {e}")

def get_top_offenders(limit=5) :
	conn = sqlite3.connect(DB_NAME)
	try :
		# Busca da nova tabela historica
		query = """
                SELECT equipamento as maquina, COUNT(*) as qtd, SUM(minutos_parado) as tempo_total
                FROM historico_paradas
                GROUP BY equipamento
                ORDER BY qtd DESC LIMIT ? \
		        """
		df = pd.read_sql_query(query, conn, params=(limit,))
	except :
		df = pd.DataFrame()
	conn.close()
	return df
