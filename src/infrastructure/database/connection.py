import sqlite3
from typing import Optional
import os


class DatabaseConnection:
    """Gerenciador de conexão com SQLite"""

    def __init__(self, db_name: str = "monitoramento.db"):
        self.db_name = db_name
        self._connection: Optional[sqlite3.Connection] = None

    def connect(self) -> sqlite3.Connection:
        """Cria ou retorna conexão existente"""
        if self._connection is None:
            # Timeout de 30s para evitar locks
            self._connection = sqlite3.connect(
                self.db_name,
                timeout=30.0,
                check_same_thread=False,
                isolation_level=None  # Autocommit mode
            )
            self._connection.row_factory = sqlite3.Row  # Permite acesso por nome de coluna

            # --- CORREÇÃO AXIOM ---
            # Ativa WAL mode para permitir leitura (Dashboard) e escrita (Service) simultâneas.
            self._connection.execute('PRAGMA journal_mode=WAL')
            # ----------------------

            # Otimizações de performance
            self._connection.execute('PRAGMA synchronous=NORMAL')  # Mais rápido, ainda seguro com WAL
            self._connection.execute('PRAGMA cache_size=-64000')    # 64MB de cache
            self._connection.execute('PRAGMA temp_store=MEMORY')    # Temp tables em memória
            self._connection.execute('PRAGMA mmap_size=268435456')  # 256MB mmap

        return self._connection

    def close(self):
        """Fecha a conexão"""
        if self._connection:
            self._connection.close()
            self._connection = None

    def init_schema(self):
        """Inicializa o schema do banco de dados"""
        conn = self.connect()
        cursor = conn.cursor()

        # Begin transaction para criação de schema
        cursor.execute('BEGIN')

        # Tabela de paradas históricas
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historico_paradas (
                uuid TEXT PRIMARY KEY,
                equipamento TEXT NOT NULL,
                planta TEXT,
                setor TEXT,
                data_inicial TEXT NOT NULL,
                data_final TEXT,
                minutos_parado REAL,
                tempo_formatado TEXT,
                motivo TEXT,
                turno TEXT,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Índices para performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_equipamento
            ON historico_paradas(equipamento)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_data_inicial
            ON historico_paradas(data_inicial)
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_data_final
            ON historico_paradas(data_final)
        ''')

        # Tabela de eventos (log bruto)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS eventos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                timestamp TEXT NOT NULL,
                maquina TEXT NOT NULL,
                status_anterior TEXT,
                status_novo TEXT NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_eventos_timestamp
            ON eventos(timestamp)
        ''')

        # Tabela de métricas diárias (nova)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS metricas_diarias (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                equipamento TEXT NOT NULL,
                data DATE NOT NULL,
                minutos_produzindo REAL DEFAULT 0,
                minutos_parado REAL DEFAULT 0,
                numero_paradas INTEGER DEFAULT 0,
                disponibilidade REAL DEFAULT 0,
                mtbf REAL DEFAULT 0,
                mttr REAL DEFAULT 0,
                created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(equipamento, data)
            )
        ''')

        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_metricas_data
            ON metricas_diarias(data)
        ''')

        conn.commit()

    def execute_query(self, query: str, params: tuple = ()):
        """Executa uma query e retorna o cursor"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        conn.commit()
        return cursor

    def fetch_all(self, query: str, params: tuple = ()):
        """Executa query e retorna todos os resultados"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchall()

    def fetch_one(self, query: str, params: tuple = ()):
        """Executa query e retorna um resultado"""
        conn = self.connect()
        cursor = conn.cursor()
        cursor.execute(query, params)
        return cursor.fetchone()