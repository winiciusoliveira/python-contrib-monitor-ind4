from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from ...domain.models import KPIData, Downtime
from ...domain.interfaces import IDowntimeRepository, IAnalyticsService


class AnalyticsService(IAnalyticsService):
    """Serviço para cálculo de KPIs e análises"""

    def __init__(self, downtime_repository: IDowntimeRepository):
        self.downtime_repo = downtime_repository

    def calculate_kpis(
        self,
        equipamento: str = None,
        data_inicio: datetime = None,
        data_fim: datetime = None
    ) -> KPIData:
        """
        Calcula KPIs para um equipamento ou período

        KPIs calculados:
        - Disponibilidade: (Tempo Produzindo / Tempo Total) × 100
        - MTBF: Mean Time Between Failures (tempo médio entre paradas)
        - MTTR: Mean Time To Repair (tempo médio de reparo/parada)
        - OEE: Overall Equipment Effectiveness
        """
        if not data_inicio:
            data_inicio = datetime.now() - timedelta(days=30)
        if not data_fim:
            data_fim = datetime.now()

        # Busca paradas do período
        if equipamento:
            paradas = self.downtime_repo.get_by_machine(equipamento, data_inicio, data_fim)
        else:
            paradas = self.downtime_repo.get_by_period(data_inicio, data_fim)

        # Filtra apenas paradas finalizadas
        paradas_finalizadas = [p for p in paradas if not p.is_ativo()]

        # Cálculos
        total_paradas = len(paradas_finalizadas)
        tempo_total_parado = sum(p.minutos_parado for p in paradas_finalizadas)

        # Tempo total do período em minutos
        periodo_total_minutos = (data_fim - data_inicio).total_seconds() / 60

        # Disponibilidade
        tempo_produzindo = periodo_total_minutos - tempo_total_parado
        disponibilidade = (tempo_produzindo / periodo_total_minutos * 100) if periodo_total_minutos > 0 else 0.0

        # MTTR (Mean Time To Repair): Tempo médio de cada parada
        mttr = (tempo_total_parado / total_paradas) if total_paradas > 0 else 0.0

        # MTBF (Mean Time Between Failures): Tempo médio entre paradas
        mtbf = (tempo_produzindo / total_paradas) if total_paradas > 0 else periodo_total_minutos

        # OEE (simplificado): Disponibilidade × Performance × Qualidade
        # Aqui estamos usando apenas disponibilidade (sem dados de performance e qualidade)
        oee = disponibilidade

        periodo_str = f"{data_inicio.strftime('%Y-%m-%d')} a {data_fim.strftime('%Y-%m-%d')}"

        return KPIData(
            disponibilidade=round(disponibilidade, 2),
            mtbf=round(mtbf, 2),
            mttr=round(mttr, 2),
            oee=round(oee, 2),
            total_paradas=total_paradas,
            tempo_total_parado=round(tempo_total_parado, 2),
            tempo_total_produzindo=round(tempo_produzindo, 2),
            periodo_analise=periodo_str
        )

    def get_top_offenders(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Retorna as máquinas com mais paradas (Top Offenders)
        """
        # Busca todas as paradas dos últimos 30 dias
        data_inicio = datetime.now() - timedelta(days=30)
        paradas = self.downtime_repo.get_by_period(data_inicio, datetime.now())

        # Agrupa por equipamento
        stats_por_equipamento: Dict[str, Dict[str, Any]] = {}

        for parada in paradas:
            if not parada.is_ativo():
                equip = parada.equipamento
                if equip not in stats_por_equipamento:
                    stats_por_equipamento[equip] = {
                        'equipamento': equip,
                        'total_paradas': 0,
                        'tempo_total': 0.0
                    }

                stats_por_equipamento[equip]['total_paradas'] += 1
                stats_por_equipamento[equip]['tempo_total'] += parada.minutos_parado

        # Ordena por número de paradas
        resultado = sorted(
            stats_por_equipamento.values(),
            key=lambda x: x['total_paradas'],
            reverse=True
        )

        return resultado[:limit]

    def get_downtime_by_turno(self, data_inicio: datetime, data_fim: datetime) -> Dict[str, float]:
        """
        Agrupa tempo de parada por turno
        """
        paradas = self.downtime_repo.get_by_period(data_inicio, data_fim)

        tempo_por_turno = {
            "TURNO 01": 0.0,
            "TURNO 02": 0.0,
            "TURNO 03": 0.0
        }

        for parada in paradas:
            if not parada.is_ativo():
                turno = parada.turno.value
                tempo_por_turno[turno] += parada.minutos_parado

        return tempo_por_turno

    def get_inactive_machines_today(self, threshold_minutes: float = 30) -> List[Dict[str, Any]]:
        """
        Retorna máquinas que ficaram paradas >= threshold hoje
        """
        hoje_inicio = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
        hoje_fim = datetime.now()

        paradas = self.downtime_repo.get_by_period(hoje_inicio, hoje_fim)

        # Agrupa por equipamento
        inatividade_por_maquina: Dict[str, Dict[str, Any]] = {}

        for parada in paradas:
            equip = parada.equipamento
            if equip not in inatividade_por_maquina:
                inatividade_por_maquina[equip] = {
                    'equipamento': equip,
                    'total_paradas': 0,
                    'tempo_total_parado': 0.0,
                    'periodos': []
                }

            duracao = parada.minutos_parado if not parada.is_ativo() else parada.calcular_duracao()

            inatividade_por_maquina[equip]['total_paradas'] += 1
            inatividade_por_maquina[equip]['tempo_total_parado'] += duracao
            inatividade_por_maquina[equip]['periodos'].append({
                'inicio': parada.data_inicial,
                'fim': parada.data_final,
                'duracao': duracao,
                'motivo': parada.motivo
            })

        # Filtra por threshold
        resultado = [
            dados for dados in inatividade_por_maquina.values()
            if dados['tempo_total_parado'] >= threshold_minutes
        ]

        # Ordena por tempo total parado
        resultado.sort(key=lambda x: x['tempo_total_parado'], reverse=True)

        return resultado
