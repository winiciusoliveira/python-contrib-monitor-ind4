from dataclasses import dataclass
from datetime import datetime
from typing import Optional, List, Dict, Any


@dataclass
class MachineStatusDTO:
    """DTO para status de máquina no dashboard"""
    nome: str
    api_id: str
    ip: str
    status: str
    status_curto: str
    cor: str
    desde: str
    unidade: str
    planta: str
    setor: str
    contador_falhas: int = 0
    is_online: bool = True
    is_produzindo: bool = False


@dataclass
class KPIFilters:
    """Filtros para cálculo de KPIs"""
    equipamento: Optional[str] = None
    unidade: Optional[str] = None
    planta: Optional[str] = None
    setor: Optional[str] = None
    data_inicio: Optional[datetime] = None
    data_fim: Optional[datetime] = None
    turno: Optional[str] = None


@dataclass
class DashboardMetrics:
    """Métricas principais do dashboard"""
    total_maquinas: int
    maquinas_produzindo: int
    maquinas_paradas: int
    maquinas_criticas: int
    disponibilidade_geral: float
    tempo_total_paradas_hoje: float  # minutos


@dataclass
class InactivityReport:
    """Relatório de inatividade de uma máquina"""
    equipamento: str
    data: datetime
    total_paradas: int
    tempo_total_parado: float  # minutos
    tempo_formatado: str
    periodos: List[Dict[str, Any]]  # Lista de períodos de parada
    percentual_inativo: float


@dataclass
class TemporalAnalysis:
    """Análise temporal de paradas"""
    periodo: str
    dados_timeline: List[Dict[str, Any]]
    distribuicao_turno: Dict[str, float]
    heatmap_data: List[Dict[str, Any]]
    tendencia: List[Dict[str, Any]]
