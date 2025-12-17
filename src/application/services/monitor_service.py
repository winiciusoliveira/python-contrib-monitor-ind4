from datetime import datetime
from typing import List, Dict, Any
import time
from ...domain.models import Machine, Downtime, Event
from ...domain.enums import MachineStatus, StatusColor, Turno
from ...domain.interfaces import IMachineRepository, IDowntimeRepository, IEventRepository, ICommunicationProtocol


class MonitorService:
    """Serviço principal de monitoramento"""

    def __init__(
        self,
        machine_repo: IMachineRepository,
        downtime_repo: IDowntimeRepository,
        event_repo: IEventRepository,
        communication_protocols: Dict[str, ICommunicationProtocol],
        limite_falhas: int = 3,
        tempo_estabilidade: int = 60
    ):
        self.machine_repo = machine_repo
        self.downtime_repo = downtime_repo
        self.event_repo = event_repo
        self.protocols = communication_protocols
        self.limite_falhas = limite_falhas
        self.tempo_estabilidade = tempo_estabilidade

        # Controle de estado
        self.inicio_paradas: Dict[str, datetime] = {}
        self.estabilidade_recuperacao: Dict[str, float] = {}

    def scan_machines(self) -> List[Machine]:
        """
        Executa scan de todas as máquinas e atualiza status
        """
        maquinas = self.machine_repo.get_all()
        timestamp_agora = datetime.now()

        for maquina in maquinas:
            # Verifica conectividade
            protocol = self.protocols.get(maquina.comunicacao.tipo.value)
            if not protocol:
                continue

            is_connected = protocol.check_connection(maquina)

            # Determina status
            status_anterior = maquina.status
            novo_status = self._determinar_status(maquina, is_connected, protocol)

            # Aplica lógica de debounce e histerese
            status_final = self._aplicar_filtros(
                maquina, status_anterior, novo_status, timestamp_agora
            )

            # Detecta mudanças e registra eventos
            if status_final != status_anterior:
                self._processar_mudanca_status(
                    maquina, status_anterior, status_final, timestamp_agora
                )

            # Atualiza máquina
            maquina.status = status_final
            self.machine_repo.update_status(maquina.api_id, {
                'status': status_final.value,
                'desde': timestamp_agora if status_final != status_anterior else maquina.desde,
                'contador_falhas': maquina.contador_falhas
            })

        return maquinas

    def _determinar_status(
        self,
        maquina: Machine,
        is_connected: bool,
        protocol: ICommunicationProtocol
    ) -> MachineStatus:
        """
        Determina o status atual da máquina baseado em comunicação
        """
        if not is_connected:
            return MachineStatus.SEM_REDE

        # Tenta ler tag de running (se configurado)
        if maquina.comunicacao.node_id:
            try:
                is_running = protocol.read_value(maquina, maquina.comunicacao.node_id)

                if is_running is True:
                    return MachineStatus.PRODUZINDO
                elif is_running is False:
                    return MachineStatus.PARADA
                else:
                    return MachineStatus.ERRO_LEITURA
            except Exception:
                return MachineStatus.FALHA_OPC

        return MachineStatus.DESCONHECIDO

    def _aplicar_filtros(
        self,
        maquina: Machine,
        status_anterior: MachineStatus,
        novo_status: MachineStatus,
        timestamp: datetime
    ) -> MachineStatus:
        """
        Aplica debounce (para SEM_REDE) e histerese (para PRODUZINDO)
        """
        # 1. Debounce de rede
        if novo_status == MachineStatus.SEM_REDE:
            maquina.contador_falhas += 1
            if maquina.contador_falhas < self.limite_falhas:
                return status_anterior  # Mantém status anterior
        else:
            maquina.contador_falhas = 0

        # 2. Histerese para retorno de produção
        if novo_status == MachineStatus.PRODUZINDO and status_anterior != MachineStatus.PRODUZINDO:
            if maquina.api_id not in self.estabilidade_recuperacao:
                self.estabilidade_recuperacao[maquina.api_id] = time.time()

            tempo_estavel = time.time() - self.estabilidade_recuperacao[maquina.api_id]
            if tempo_estavel < self.tempo_estabilidade:
                return status_anterior  # Aguarda estabilização

            # Confirmou retorno, limpa controle
            self.estabilidade_recuperacao.pop(maquina.api_id, None)

        return novo_status

    def _processar_mudanca_status(
        self,
        maquina: Machine,
        status_anterior: MachineStatus,
        status_novo: MachineStatus,
        timestamp: datetime
    ):
        """
        Processa mudança de status, registrando eventos e paradas
        """
        # Registra evento
        event = Event(
            timestamp=timestamp,
            maquina=maquina.nome,
            status_anterior=status_anterior.value,
            status_novo=status_novo.value
        )
        self.event_repo.save(event)

        # Lógica de paradas
        # Se estava produzindo e agora parou
        if status_anterior == MachineStatus.PRODUZINDO and status_novo != MachineStatus.PRODUZINDO:
            self.inicio_paradas[maquina.api_id] = timestamp

        # Se estava parado e voltou a produzir
        elif status_novo == MachineStatus.PRODUZINDO and status_anterior != MachineStatus.PRODUZINDO:
            if maquina.api_id in self.inicio_paradas:
                dt_inicio = self.inicio_paradas.pop(maquina.api_id)

                # Calcula turno
                turno = self._calcular_turno(dt_inicio)

                # Cria downtime
                downtime = Downtime(
                    uuid="",  # Será gerado no repositório
                    equipamento=maquina.nome,
                    hierarquia=maquina.hierarquia,
                    data_inicial=dt_inicio,
                    data_final=timestamp,
                    motivo=status_anterior.value,
                    turno=turno
                )

                # Calcula duração
                downtime.minutos_parado = downtime.calcular_duracao()
                downtime.tempo_formatado = self._formatar_duracao(
                    (timestamp - dt_inicio).total_seconds()
                )

                # Salva no banco
                self.downtime_repo.save(downtime)

    def _calcular_turno(self, dt: datetime) -> Turno:
        """Calcula o turno baseado no horário"""
        t = dt.time()
        minutos = t.hour * 60 + t.minute

        t1_start = 6 * 60  # 06:00
        t2_start = 14 * 60 + 30  # 14:30
        t3_start = 22 * 60 + 52  # 22:52

        if t1_start <= minutos < t2_start:
            return Turno.T1
        elif t2_start <= minutos < t3_start:
            return Turno.T2
        else:
            return Turno.T3

    def _formatar_duracao(self, segundos: float) -> str:
        """Formata duração em dd-hh:mm:ss"""
        m, s = divmod(segundos, 60)
        h, m = divmod(m, 60)
        d, h = divmod(h, 24)
        if d > 0:
            return f"{int(d):02d}-{int(h):02d}:{int(m):02d}:{int(s):02d}"
        return f"{int(h):02d}:{int(m):02d}:{int(s):02d}"

    def get_dashboard_metrics(self) -> Dict[str, Any]:
        """
        Retorna métricas para o dashboard
        """
        maquinas = self.machine_repo.get_all()

        total = len(maquinas)
        produzindo = sum(1 for m in maquinas if m.status == MachineStatus.PRODUZINDO)
        paradas = sum(1 for m in maquinas if m.status == MachineStatus.PARADA)
        criticas = sum(1 for m in maquinas if m.status in [MachineStatus.SEM_REDE, MachineStatus.FALHA_OPC])

        disponibilidade = (produzindo / total * 100) if total > 0 else 0.0

        return {
            'total_maquinas': total,
            'maquinas_produzindo': produzindo,
            'maquinas_paradas': paradas,
            'maquinas_criticas': criticas,
            'disponibilidade_geral': round(disponibilidade, 2)
        }
