from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from datetime import datetime
from .models import Machine, Downtime, Event, KPIData


class ICommunicationProtocol(ABC):
    """Interface para protocolos de comunicação"""

    @abstractmethod
    def read_value(self, machine: Machine, tag: str) -> Optional[Any]:
        """Lê um valor de uma tag"""
        pass

    @abstractmethod
    def write_value(self, machine: Machine, tag: str, value: Any) -> bool:
        """Escreve um valor em uma tag"""
        pass

    @abstractmethod
    def check_connection(self, machine: Machine) -> bool:
        """Verifica se há conexão com a máquina"""
        pass


class IMachineRepository(ABC):
    """Interface para repositório de máquinas"""

    @abstractmethod
    def get_all(self) -> List[Machine]:
        """Retorna todas as máquinas"""
        pass

    @abstractmethod
    def get_by_id(self, api_id: str) -> Optional[Machine]:
        """Busca máquina por ID"""
        pass

    @abstractmethod
    def get_by_hierarquia(self, unidade: str = None, planta: str = None, setor: str = None) -> List[Machine]:
        """Busca máquinas por hierarquia"""
        pass

    @abstractmethod
    def save(self, machine: Machine) -> None:
        """Salva uma máquina"""
        pass

    @abstractmethod
    def update_status(self, api_id: str, status: Dict[str, Any]) -> None:
        """Atualiza status de uma máquina"""
        pass


class IDowntimeRepository(ABC):
    """Interface para repositório de paradas"""

    @abstractmethod
    def save(self, downtime: Downtime) -> str:
        """Salva uma parada e retorna UUID"""
        pass

    @abstractmethod
    def get_by_machine(self, equipamento: str, data_inicio: datetime = None, data_fim: datetime = None) -> List[Downtime]:
        """Busca paradas de uma máquina"""
        pass

    @abstractmethod
    def get_active_downtimes(self) -> List[Downtime]:
        """Retorna paradas ativas"""
        pass

    @abstractmethod
    def get_by_period(self, data_inicio: datetime, data_fim: datetime) -> List[Downtime]:
        """Busca paradas em um período"""
        pass

    @abstractmethod
    def finalize_downtime(self, uuid: str, data_final: datetime) -> None:
        """Finaliza uma parada"""
        pass


class IEventRepository(ABC):
    """Interface para repositório de eventos"""

    @abstractmethod
    def save(self, event: Event) -> None:
        """Salva um evento"""
        pass

    @abstractmethod
    def get_recent(self, limit: int = 100) -> List[Event]:
        """Retorna eventos recentes"""
        pass


class IAnalyticsService(ABC):
    """Interface para serviço de analytics"""

    @abstractmethod
    def calculate_kpis(self, equipamento: str = None, data_inicio: datetime = None, data_fim: datetime = None) -> KPIData:
        """Calcula KPIs para um equipamento ou período"""
        pass

    @abstractmethod
    def get_top_offenders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna máquinas com mais paradas"""
        pass

    @abstractmethod
    def get_downtime_by_turno(self, data_inicio: datetime, data_fim: datetime) -> Dict[str, float]:
        """Agrupa tempo de parada por turno"""
        pass


class INotificationService(ABC):
    """Interface para serviço de notificações"""

    @abstractmethod
    def send(self, message: str, level: str = "INFO") -> bool:
        """Envia uma notificação"""
        pass

    @abstractmethod
    def send_filtered(self, message: str, motivo: str, duracao_minutos: float) -> bool:
        """Envia notificação com filtros inteligentes"""
        pass
