from enum import Enum


class MachineStatus(Enum):
    """Status possíveis de uma máquina"""
    PRODUZINDO = "PRODUZINDO"
    PARADA = "PARADA"
    SEM_REDE = "SEM REDE"
    FALHA_OPC = "FALHA OPC"
    ERRO_LEITURA = "ERRO LEITURA TAG"
    DESCONHECIDO = "DESCONHECIDO"
    AGUARDANDO = "AGUARDANDO"


class CommunicationType(Enum):
    """Tipos de protocolos de comunicação suportados"""
    OPC_UA = "OPC_UA"
    MODBUS_TCP = "MODBUS_TCP"
    MQTT = "MQTT"
    REST_API = "REST_API"
    NETWORK_PING = "NETWORK_PING"


class Turno(Enum):
    """Turnos de trabalho"""
    T1 = "TURNO 01"  # 06:00 - 14:30
    T2 = "TURNO 02"  # 14:30 - 22:52
    T3 = "TURNO 03"  # 22:52 - 06:00


class NotificationLevel(Enum):
    """Níveis de notificação"""
    INFO = "INFO"
    WARNING = "WARNING"
    CRITICAL = "CRITICAL"
    SUCCESS = "SUCCESS"


class StatusColor(Enum):
    """Cores associadas aos status"""
    GREEN = "#28a745"
    RED = "#dc3545"
    YELLOW = "#ffc107"
    ORANGE = "#fd7e14"
    GRAY = "#808080"
