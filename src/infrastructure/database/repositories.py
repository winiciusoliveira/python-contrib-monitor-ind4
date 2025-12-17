from typing import List, Optional, Dict, Any
from datetime import datetime
import uuid
import json
import os
from .connection import DatabaseConnection
from ...domain.models import Machine, Downtime, Event, Hierarquia, CommunicationConfig
from ...domain.enums import MachineStatus, CommunicationType, Turno
from ...domain.interfaces import IMachineRepository, IDowntimeRepository, IEventRepository


def parse_datetime_safe(date_string: str) -> Optional[datetime]:
    """
    Parse datetime com suporte a microssegundos ou sem
    """
    if not date_string:
        return None

    # Tenta com microssegundos primeiro
    formats = [
        '%Y-%m-%d %H:%M:%S.%f',  # Com microssegundos
        '%Y-%m-%d %H:%M:%S',      # Sem microssegundos
    ]

    for fmt in formats:
        try:
            return datetime.strptime(date_string, fmt)
        except ValueError:
            continue

    # Se nenhum formato funcionar, retorna None
    return None


class MachineRepository(IMachineRepository):
    """Repositório de máquinas usando JSON + Estado em memória"""

    def __init__(self, config_file: str = "config.json", state_file: str = "estado_atual.json"):
        self.config_file = config_file
        self.state_file = state_file
        self._machines_cache: Dict[str, Machine] = {}
        self._load_machines()

    def _load_machines(self):
        """Carrega máquinas do arquivo de configuração"""
        if not os.path.exists(self.config_file):
            return

        with open(self.config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)

        for item in config_data:
            hierarquia = Hierarquia(
                unidade=item.get('unidade', 'Geral'),
                planta=item.get('planta', 'Geral'),
                setor=item.get('setor', 'Geral')
            )

            # Lê node_id do config.json (consolidado - Single Source of Truth)
            comunicacao = CommunicationConfig(
                tipo=CommunicationType.OPC_UA,  # Padrão
                endpoint=f"opc.tcp://{item['ip']}:{item.get('porta', 4840)}",
                porta=item.get('porta', 4840),
                node_id=item.get('node_id')  # Agora vem do config.json
            )

            machine = Machine(
                nome=item['nome'],
                api_id=item['api_id'],
                ip=item['ip'],
                hierarquia=hierarquia,
                comunicacao=comunicacao
            )

            self._machines_cache[machine.api_id] = machine

        # Carrega estado persistente
        self._load_state()

    def _load_state(self):
        """Carrega estado atual das máquinas"""
        if not os.path.exists(self.state_file):
            return

        try:
            with open(self.state_file, 'r', encoding='utf-8') as f:
                state_data = json.load(f)

            maquinas_state = state_data.get('maquinas', {})

            for api_id, state in maquinas_state.items():
                if api_id in self._machines_cache:
                    machine = self._machines_cache[api_id]

                    # Atualiza status
                    status_str = state.get('status', 'DESCONHECIDO')
                    try:
                        machine.status = MachineStatus(status_str)
                    except ValueError:
                        machine.status = MachineStatus.DESCONHECIDO

                    machine.status_descricao = state.get('status', '')
                    machine.cor = state.get('cor', '#808080')
                    machine.contador_falhas = state.get('contador', 0)

                    desde_str = state.get('desde')
                    if desde_str:
                        machine.desde = parse_datetime_safe(desde_str) or datetime.now()
        except Exception as e:
            print(f"Erro ao carregar estado: {e}")

    def save_state(self):
        """Salva estado atual no arquivo JSON"""
        maquinas_dict = {}

        for api_id, machine in self._machines_cache.items():
            # Remove microssegundos antes de salvar
            desde_str = machine.desde.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S') if machine.desde else ''

            maquinas_dict[api_id] = {
                'status': machine.status.value,
                'cor': machine.cor,
                'desde': desde_str,
                'contador': machine.contador_falhas,
                'ip': machine.ip,
                'unidade': machine.hierarquia.unidade,
                'planta': machine.hierarquia.planta,
                'setor': machine.hierarquia.setor
            }

        # Remove microssegundos do timestamp de metadata também
        ultimo_sinal = datetime.now().replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')

        data = {
            "metadata": {
                "ultimo_sinal": ultimo_sinal,
                "status_servico": "RODANDO",
                "versao": "2.0 (Clean Architecture)"
            },
            "maquinas": maquinas_dict
        }

        with open(self.state_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

    def get_all(self) -> List[Machine]:
        return list(self._machines_cache.values())

    def get_by_id(self, api_id: str) -> Optional[Machine]:
        return self._machines_cache.get(api_id)

    def get_by_hierarquia(
        self,
        unidade: str = None,
        planta: str = None,
        setor: str = None
    ) -> List[Machine]:
        resultado = []

        for machine in self._machines_cache.values():
            if unidade and machine.hierarquia.unidade != unidade:
                continue
            if planta and machine.hierarquia.planta != planta:
                continue
            if setor and machine.hierarquia.setor != setor:
                continue

            resultado.append(machine)

        return resultado

    def save(self, machine: Machine) -> None:
        self._machines_cache[machine.api_id] = machine
        self.save_state()

    def update_status(self, api_id: str, status: Dict[str, Any]) -> None:
        if api_id in self._machines_cache:
            machine = self._machines_cache[api_id]

            if 'status' in status:
                try:
                    machine.status = MachineStatus(status['status'])
                except ValueError:
                    pass

            if 'desde' in status:
                machine.desde = status['desde']

            if 'contador_falhas' in status:
                machine.contador_falhas = status['contador_falhas']

            if 'cor' in status:
                machine.cor = status['cor']

            self.save_state()


class DowntimeRepository(IDowntimeRepository):
    """Repositório de paradas usando SQLite"""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    def save(self, downtime: Downtime) -> str:
        """Salva uma parada e retorna UUID"""
        if not downtime.uuid:
            downtime.uuid = str(uuid.uuid4())

        query = '''
            INSERT INTO historico_paradas
            (uuid, equipamento, planta, setor, data_inicial, data_final,
             minutos_parado, tempo_formatado, motivo, turno)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        '''

        # Remove microssegundos antes de salvar
        data_inicial_str = downtime.data_inicial.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        data_final_str = downtime.data_final.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S') if downtime.data_final else None

        params = (
            downtime.uuid,
            downtime.equipamento,
            downtime.hierarquia.planta,
            downtime.hierarquia.setor,
            data_inicial_str,
            data_final_str,
            downtime.minutos_parado,
            downtime.tempo_formatado,
            downtime.motivo,
            downtime.turno.value
        )

        self.db.execute_query(query, params)
        return downtime.uuid

    def get_by_machine(
        self,
        equipamento: str,
        data_inicio: datetime = None,
        data_fim: datetime = None
    ) -> List[Downtime]:
        """Busca paradas de uma máquina"""
        query = 'SELECT * FROM historico_paradas WHERE equipamento = ?'
        params = [equipamento]

        if data_inicio:
            query += ' AND data_inicial >= ?'
            params.append(data_inicio.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S'))

        if data_fim:
            query += ' AND data_inicial <= ?'
            params.append(data_fim.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S'))

        query += ' ORDER BY data_inicial DESC'

        rows = self.db.fetch_all(query, tuple(params))
        return [self._row_to_downtime(row) for row in rows]

    def get_active_downtimes(self) -> List[Downtime]:
        """Retorna paradas ativas (sem data_final)"""
        query = 'SELECT * FROM historico_paradas WHERE data_final IS NULL'
        rows = self.db.fetch_all(query)
        return [self._row_to_downtime(row) for row in rows]

    def get_by_period(self, data_inicio: datetime, data_fim: datetime) -> List[Downtime]:
        """Busca paradas em um período"""
        query = '''
            SELECT * FROM historico_paradas
            WHERE data_inicial >= ? AND data_inicial <= ?
            ORDER BY data_inicial DESC
        '''
        params = (
            data_inicio.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S'),
            data_fim.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        )

        rows = self.db.fetch_all(query, params)
        return [self._row_to_downtime(row) for row in rows]

    def finalize_downtime(self, uuid: str, data_final: datetime) -> None:
        """Finaliza uma parada"""
        query = 'UPDATE historico_paradas SET data_final = ? WHERE uuid = ?'
        # Remove microssegundos antes de salvar
        data_final_str = data_final.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        params = (data_final_str, uuid)
        self.db.execute_query(query, params)

    def _row_to_downtime(self, row) -> Downtime:
        """Converte row do SQLite para Downtime"""
        hierarquia = Hierarquia(
            planta=row['planta'] or 'Geral',
            setor=row['setor'] or 'Geral'
        )

        data_final = None
        if row['data_final']:
            data_final = parse_datetime_safe(row['data_final'])

        turno = Turno.T1
        try:
            turno = Turno(row['turno'])
        except:
            pass

        data_inicial = parse_datetime_safe(row['data_inicial']) or datetime.now()

        return Downtime(
            uuid=row['uuid'],
            equipamento=row['equipamento'],
            hierarquia=hierarquia,
            data_inicial=data_inicial,
            data_final=data_final,
            minutos_parado=row['minutos_parado'] or 0.0,
            tempo_formatado=row['tempo_formatado'] or '',
            motivo=row['motivo'] or '',
            turno=turno
        )


class EventRepository(IEventRepository):
    """Repositório de eventos usando SQLite"""

    def __init__(self, db: DatabaseConnection):
        self.db = db

    def save(self, event: Event) -> None:
        """Salva um evento"""
        query = '''
            INSERT INTO eventos (timestamp, maquina, status_anterior, status_novo)
            VALUES (?, ?, ?, ?)
        '''
        # Remove microssegundos antes de salvar
        timestamp_str = event.timestamp.replace(microsecond=0).strftime('%Y-%m-%d %H:%M:%S')
        params = (
            timestamp_str,
            event.maquina,
            event.status_anterior,
            event.status_novo
        )
        self.db.execute_query(query, params)

    def get_recent(self, limit: int = 100) -> List[Event]:
        """Retorna eventos recentes"""
        query = 'SELECT * FROM eventos ORDER BY timestamp DESC LIMIT ?'
        rows = self.db.fetch_all(query, (limit,))

        eventos = []
        for row in rows:
            timestamp = parse_datetime_safe(row['timestamp']) or datetime.now()
            evento = Event(
                timestamp=timestamp,
                maquina=row['maquina'],
                status_anterior=row['status_anterior'] or '',
                status_novo=row['status_novo']
            )
            eventos.append(evento)

        return eventos
