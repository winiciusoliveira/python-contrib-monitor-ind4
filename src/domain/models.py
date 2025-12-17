from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any
from .enums import MachineStatus, CommunicationType, Turno


@dataclass
class Hierarquia:
    """Representa a hierarquia organizacional"""
    unidade: str = "Geral"
    planta: str = "Geral"
    setor: str = "Geral"


@dataclass
class CommunicationConfig:
    """Configuração de comunicação de uma máquina"""
    tipo: CommunicationType
    endpoint: str
    porta: Optional[int] = None
    node_id: Optional[str] = None
    parametros: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Machine:
    """Entidade que representa uma máquina industrial"""
    nome: str
    api_id: str
    ip: str
    hierarquia: Hierarquia
    comunicacao: CommunicationConfig
    status: MachineStatus = MachineStatus.DESCONHECIDO
    status_descricao: str = ""
    cor: str = "#808080"
    desde: Optional[datetime] = None
    contador_falhas: int = 0
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def nome_completo(self) -> str:
        """Retorna nome completo com hierarquia"""
        return f"{self.hierarquia.unidade}/{self.hierarquia.planta}/{self.hierarquia.setor}/{self.nome}"

    def is_online(self) -> bool:
        """Verifica se a máquina está online"""
        return self.status not in [MachineStatus.SEM_REDE, MachineStatus.FALHA_OPC]

    def is_produzindo(self) -> bool:
        """Verifica se está produzindo"""
        return self.status == MachineStatus.PRODUZINDO


@dataclass
class Downtime:
    """Representa um período de parada"""
    uuid: str
    equipamento: str
    hierarquia: Hierarquia
    data_inicial: datetime
    data_final: Optional[datetime] = None
    minutos_parado: float = 0.0
    tempo_formatado: str = ""
    motivo: str = ""
    turno: Turno = Turno.T1
    metadata: Dict[str, Any] = field(default_factory=dict)

    def is_ativo(self) -> bool:
        """Verifica se a parada ainda está ativa"""
        return self.data_final is None

    def calcular_duracao(self) -> float:
        """Calcula a duração em minutos"""
        if self.data_final:
            delta = self.data_final - self.data_inicial
            return delta.total_seconds() / 60
        return 0.0


@dataclass
class Event:
    """Evento de mudança de status"""
    timestamp: datetime
    maquina: str
    status_anterior: str
    status_novo: str
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class KPIData:
    """KPIs de uma máquina ou grupo"""
    disponibilidade: float = 0.0  # Percentual
    mtbf: float = 0.0  # Mean Time Between Failures (minutos)
    mttr: float = 0.0  # Mean Time To Repair (minutos)
    oee: float = 0.0  # Overall Equipment Effectiveness (%)
    total_paradas: int = 0
    tempo_total_parado: float = 0.0  # minutos
    tempo_total_produzindo: float = 0.0  # minutos
    periodo_analise: str = ""
