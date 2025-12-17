import streamlit as st
import sys
import os
from datetime import datetime, timedelta
import pandas as pd

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importações da nova arquitetura
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.repositories import MachineRepository, DowntimeRepository, EventRepository
from src.application.services.analytics_service import AnalyticsService
from src.presentation.components.metrics_card import render_kpi_row, render_status_badge, render_progress_bar
from src.presentation.components.machine_card import render_machine_card
from src.presentation.components.charts import (
    render_bar_chart, render_pie_chart, render_pareto_chart,
    render_timeline_chart, render_heatmap, render_line_chart
)

# ============== CONFIGURAÇÃO ==============
st.set_page_config(
    page_title="Monitoramento Industrial 4.0",
    layout="wide",
    page_icon="🏭",
    initial_sidebar_state="expanded"
)

# ============== CSS CUSTOMIZADO ==============
css_rules = """
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 3rem;}

    .stApp {
        background-color: #f3f4f6;
        color: #1f2937;
    }

    [data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff !important;
        border: 1px solid #d1d5db !important;
        box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.1), 0 1px 2px -1px rgba(0, 0, 0, 0.1) !important;
        border-radius: 8px !important;
        padding: 1rem !important;
    }

    h1, h2, h3, h4, h5, h6 {
        color: #111827 !important;
        font-family: sans-serif;
    }

    p, .stMarkdown {
        color: #374151 !important;
    }

    [data-testid="stMetricLabel"] {
        color: #6b7280 !important;
        font-size: 14px;
    }

    [data-testid="stMetricValue"] {
        color: #000000 !important;
        font-weight: 700;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        height: 50px;
        padding-left: 20px;
        padding-right: 20px;
        background-color: #ffffff;
        border-radius: 8px 8px 0 0;
        border: 1px solid #d1d5db;
        border-bottom: none;
    }

    .stTabs [aria-selected="true"] {
        background-color: #f3f4f6;
        border-color: #2563eb;
        border-bottom: 2px solid #2563eb;
    }
"""
st.markdown(f"<style>{css_rules}</style>", unsafe_allow_html=True)

# ============== INICIALIZAÇÃO ==============
@st.cache_resource
def init_services():
    """Inicializa serviços (singleton)"""
    db = DatabaseConnection()
    db.init_schema()

    machine_repo = MachineRepository()
    downtime_repo = DowntimeRepository(db)
    event_repo = EventRepository(db)
    analytics_service = AnalyticsService(downtime_repo)

    return {
        'machine_repo': machine_repo,
        'downtime_repo': downtime_repo,
        'event_repo': event_repo,
        'analytics_service': analytics_service
    }

services = init_services()
machine_repo = services['machine_repo']
downtime_repo = services['downtime_repo']
analytics_service = services['analytics_service']

# ============== CABEÇALHO ==============
st.title("🏭 Monitoramento Industrial 4.0")

# Auto-refresh a cada 5 segundos
from streamlit_autorefresh import st_autorefresh
st_autorefresh(interval=5000, key="ui_refresh")

# ============== CARREGA DADOS ==============
maquinas = machine_repo.get_all()

if not maquinas:
    st.info("⏳ Aguardando dados do serviço de monitoramento...")
    st.stop()

# ============== SIDEBAR - FILTROS ==============
with st.sidebar:
    st.header("🔍 Filtros Globais")

    # Filtro por Unidade
    unidades = sorted(list(set([m.hierarquia.unidade for m in maquinas])))
    sel_unidades = st.multiselect("Unidade:", options=unidades, default=unidades)

    # Filtra máquinas por unidade
    maquinas_filtradas = [m for m in maquinas if m.hierarquia.unidade in sel_unidades]

    # Filtro por Planta
    plantas = sorted(list(set([m.hierarquia.planta for m in maquinas_filtradas])))
    sel_plantas = st.multiselect("Planta:", options=plantas, default=plantas)

    # Filtra por planta
    maquinas_filtradas = [m for m in maquinas_filtradas if m.hierarquia.planta in sel_plantas]

    # Filtro por Setor
    setores = sorted(list(set([m.hierarquia.setor for m in maquinas_filtradas])))
    sel_setores = st.multiselect("Setor:", options=setores, default=setores)

    # Filtra por setor
    maquinas_filtradas = [m for m in maquinas_filtradas if m.hierarquia.setor in sel_setores]

    st.divider()

    # Filtros de período para análises
    st.subheader("📅 Período de Análise")
    periodo_dias = st.selectbox(
        "Período:",
        options=[1, 7, 15, 30, 90],
        format_func=lambda x: f"Últimos {x} dias",
        index=3  # Padrão: 30 dias
    )

    data_fim = datetime.now()
    data_inicio = data_fim - timedelta(days=periodo_dias)

# ============== ABAS PRINCIPAIS ==============
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 Visão Geral",
    "🔍 Detalhes",
    "📈 Análise Temporal",
    "📜 Histórico",
    "⚙️ Configuração"
])

# ============== ABA 1: VISÃO GERAL ==============
with tab1:
    st.header("Visão Geral do Sistema")

    # KPIs Principais
    total_maquinas = len(maquinas_filtradas)
    maquinas_produzindo = sum(1 for m in maquinas_filtradas if "PRODUZINDO" in m.status.value)
    maquinas_paradas = sum(1 for m in maquinas_filtradas if m.status.value == "PARADA")
    maquinas_criticas = sum(1 for m in maquinas_filtradas if m.status.value in ["SEM REDE", "FALHA OPC"])

    disponibilidade_geral = (maquinas_produzindo / total_maquinas * 100) if total_maquinas > 0 else 0.0

    # Renderiza KPIs
    col1, col2, col3, col4, col5 = st.columns(5)

    with col1:
        with st.container(border=True):
            st.metric("Total de Máquinas", total_maquinas)

    with col2:
        with st.container(border=True):
            st.metric("🟢 Produzindo", maquinas_produzindo)

    with col3:
        with st.container(border=True):
            st.metric("🔴 Paradas", maquinas_paradas)

    with col4:
        with st.container(border=True):
            st.metric("⚠️ Críticas", maquinas_criticas)

    with col5:
        with st.container(border=True):
            st.metric("📊 Disponibilidade", f"{disponibilidade_geral:.1f}%")

    st.divider()

    # Distribuição de Status
    col_left, col_right = st.columns(2)

    with col_left:
        st.subheader("📊 Distribuição de Status")

        status_count = {}
        for m in maquinas_filtradas:
            status = m.status.value
            status_count[status] = status_count.get(status, 0) + 1

        if status_count:
            df_status = pd.DataFrame(list(status_count.items()), columns=['Status', 'Quantidade'])
            render_pie_chart(df_status, 'Quantidade', 'Status', 'Distribuição por Status')

    with col_right:
        st.subheader("🏭 Disponibilidade por Setor")

        # Calcula disponibilidade por setor
        setor_stats = {}
        for m in maquinas_filtradas:
            setor = m.hierarquia.setor
            if setor not in setor_stats:
                setor_stats[setor] = {'total': 0, 'produzindo': 0}

            setor_stats[setor]['total'] += 1
            if "PRODUZINDO" in m.status.value:
                setor_stats[setor]['produzindo'] += 1

        for setor, stats in setor_stats.items():
            disp = (stats['produzindo'] / stats['total'] * 100) if stats['total'] > 0 else 0
            render_progress_bar(
                disp,
                100,
                f"{setor} ({stats['produzindo']}/{stats['total']})",
                "#28a745" if disp >= 75 else "#ffc107" if disp >= 50 else "#dc3545"
            )

    st.divider()

    # Máquinas com mais tempo paradas HOJE
    st.subheader("⚠️ Máquinas Inativas Hoje (> 30 min)")

    inativas_hoje = analytics_service.get_inactive_machines_today(threshold_minutes=30)

    if inativas_hoje:
        for maq_data in inativas_hoje[:5]:  # Top 5
            with st.container(border=True):
                col_a, col_b, col_c = st.columns([2, 1, 1])

                with col_a:
                    st.markdown(f"**{maq_data['equipamento']}**")

                with col_b:
                    st.metric("Tempo Total Parado", f"{maq_data['tempo_total_parado']:.0f} min")

                with col_c:
                    st.metric("Nº de Paradas", maq_data['total_paradas'])

                # Detalhes das paradas
                with st.expander("Ver períodos"):
                    for periodo in maq_data['periodos']:
                        st.caption(
                            f"🕒 {periodo['inicio'].strftime('%H:%M')} - "
                            f"{periodo['fim'].strftime('%H:%M') if periodo['fim'] else 'Agora'}: "
                            f"{periodo['duracao']:.0f} min ({periodo['motivo']})"
                        )
    else:
        st.success("✅ Nenhuma máquina inativa por mais de 30 minutos hoje!")

# ============== ABA 2: DETALHES ==============
with tab2:
    st.header("Detalhes por Hierarquia")

    # Seletor de visualização
    modo_view = st.radio("Modo de visualização:", ["📱 Cards", "🖥️ Tabela"], horizontal=True)

    if modo_view == "📱 Cards":
        if not maquinas_filtradas:
            st.info("Nenhuma máquina com os filtros selecionados")
        else:
            cols = st.columns(2)
            for idx, maq in enumerate(maquinas_filtradas):
                with cols[idx % 2]:
                    render_machine_card(
                        nome=maq.nome,
                        status=maq.status.value,
                        desde=maq.desde.strftime('%H:%M:%S') if maq.desde else '-',
                        setor=maq.hierarquia.setor,
                        ip=maq.ip
                    )
    else:
        # Modo Tabela
        df_data = []
        for maq in maquinas_filtradas:
            df_data.append({
                'Máquina': maq.nome,
                'Status': maq.status.value,
                'IP': maq.ip,
                'Setor': maq.hierarquia.setor,
                'Planta': maq.hierarquia.planta,
                'Desde': maq.desde.strftime('%H:%M:%S') if maq.desde else '-'
            })

        df = pd.DataFrame(df_data)
        st.dataframe(df, use_container_width=True, height=600, hide_index=True)

# ============== ABA 3: ANÁLISE TEMPORAL ==============
with tab3:
    st.header("Análise Temporal de Paradas")

    st.info(f"📅 Analisando período de {data_inicio.strftime('%d/%m/%Y')} a {data_fim.strftime('%d/%m/%Y')}")

    # Top Offenders (Pareto)
    st.subheader("🏆 Top 10 Máquinas com Mais Paradas")

    top_offenders = analytics_service.get_top_offenders(limit=10)

    if top_offenders:
        df_top = pd.DataFrame(top_offenders)
        render_pareto_chart(
            df_top,
            'equipamento',
            'total_paradas',
            'Análise de Pareto - Máquinas com Mais Paradas'
        )

        # Tabela detalhada
        st.dataframe(df_top, use_container_width=True, hide_index=True)
    else:
        st.info("Sem dados de paradas no período selecionado")

    st.divider()

    # Distribuição por Turno
    st.subheader("🌓 Distribuição de Paradas por Turno")

    tempo_por_turno = analytics_service.get_downtime_by_turno(data_inicio, data_fim)

    if any(tempo_por_turno.values()):
        df_turno = pd.DataFrame(list(tempo_por_turno.items()), columns=['Turno', 'Tempo (min)'])
        render_bar_chart(df_turno, 'Turno', 'Tempo (min)', 'Tempo de Paradas por Turno')
    else:
        st.info("Sem dados de turnos no período")

# ============== ABA 4: HISTÓRICO ==============
with tab4:
    st.header("Histórico Completo de Paradas")

    # Filtros adicionais
    col_f1, col_f2 = st.columns(2)

    with col_f1:
        equipamento_filter = st.selectbox(
            "Filtrar por Equipamento:",
            options=["Todos"] + [m.nome for m in maquinas_filtradas]
        )

    with col_f2:
        min_duracao = st.number_input("Duração mínima (min):", min_value=0, value=0)

    # Busca histórico
    if equipamento_filter == "Todos":
        historico = downtime_repo.get_by_period(data_inicio, data_fim)
    else:
        historico = downtime_repo.get_by_machine(equipamento_filter, data_inicio, data_fim)

    # Filtra por duração
    historico_filtrado = [h for h in historico if h.minutos_parado >= min_duracao and not h.is_ativo()]

    st.metric("Total de Paradas no Período", len(historico_filtrado))

    if historico_filtrado:
        # Converte para DataFrame
        df_hist = []
        for h in historico_filtrado:
            df_hist.append({
                'Equipamento': h.equipamento,
                'Data/Hora Inicial': h.data_inicial.strftime('%d/%m/%Y %H:%M'),
                'Data/Hora Final': h.data_final.strftime('%d/%m/%Y %H:%M') if h.data_final else '-',
                'Duração (min)': round(h.minutos_parado, 2),
                'Tempo Formatado': h.tempo_formatado,
                'Motivo': h.motivo,
                'Turno': h.turno.value,
                'Setor': h.hierarquia.setor
            })

        df_historico = pd.DataFrame(df_hist)

        st.dataframe(
            df_historico,
            use_container_width=True,
            height=500,
            hide_index=True
        )

        # Botão de export
        csv = df_historico.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download CSV",
            data=csv,
            file_name=f"historico_paradas_{datetime.now().strftime('%Y%m%d')}.csv",
            mime='text/csv'
        )
    else:
        st.info("Nenhuma parada encontrada com os filtros selecionados")

# ============== ABA 5: CONFIGURAÇÃO ==============
with tab5:
    st.header("Configuração e Diagnóstico")

    st.subheader("🔧 Informações do Sistema")

    col_info1, col_info2 = st.columns(2)

    with col_info1:
        with st.container(border=True):
            st.metric("Total de Máquinas Configuradas", len(maquinas))
            st.metric("Banco de Dados", "SQLite")
            st.metric("Versão", "2.0 - Clean Architecture")

    with col_info2:
        with st.container(border=True):
            st.metric("Último Scan", datetime.now().strftime('%H:%M:%S'))
            st.metric("Status do Serviço", "🟢 Rodando")

    st.divider()

    st.subheader("🧪 Testes de Conectividade")

    st.info("Funcionalidade em desenvolvimento: Teste individual de conectividade OPC")

    # TODO: Adicionar interface para escrita de tags OPC
    st.divider()

    st.subheader("📝 Logs Recentes")
    st.info("Funcionalidade em desenvolvimento: Visualização de logs do sistema")
