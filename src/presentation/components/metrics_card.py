import streamlit as st
from typing import Optional


def render_metric_card(
    label: str,
    value: any,
    delta: Optional[str] = None,
    help_text: Optional[str] = None,
    border: bool = True
):
    """
    Renderiza um card de métrica padronizado

    Args:
        label: Rótulo da métrica
        value: Valor principal
        delta: Variação (opcional)
        help_text: Texto de ajuda (opcional)
        border: Se deve exibir borda
    """
    if border:
        with st.container(border=True):
            st.metric(label=label, value=value, delta=delta, help=help_text)
    else:
        st.metric(label=label, value=value, delta=delta, help=help_text)


def render_kpi_row(kpis: dict):
    """
    Renderiza uma linha de KPIs

    Args:
        kpis: Dicionário com {label: value}
    """
    num_kpis = len(kpis)
    cols = st.columns(num_kpis)

    for idx, (label, value) in enumerate(kpis.items()):
        with cols[idx]:
            with st.container(border=True):
                st.metric(label=label, value=value)


def render_status_badge(status: str, count: int = None) -> str:
    """
    Retorna HTML para badge de status

    Args:
        status: Status da máquina
        count: Quantidade (opcional)

    Returns:
        String HTML do badge
    """
    color_map = {
        'PRODUZINDO': '#28a745',
        'PARADA': '#dc3545',
        'SEM REDE': '#6c757d',
        'FALHA OPC': '#ffc107',
        'ERRO LEITURA': '#fd7e14'
    }

    color = color_map.get(status.upper(), '#808080')
    text = f"{status} ({count})" if count is not None else status

    return f"""
    <span style="
        background-color: {color};
        color: white;
        padding: 4px 12px;
        border-radius: 12px;
        font-size: 14px;
        font-weight: 600;
        display: inline-block;
        margin: 2px;
    ">
        {text}
    </span>
    """


def render_progress_bar(value: float, max_value: float = 100, label: str = "", color: str = "#28a745"):
    """
    Renderiza uma barra de progresso customizada

    Args:
        value: Valor atual
        max_value: Valor máximo
        label: Rótulo (opcional)
        color: Cor da barra
    """
    percentage = (value / max_value * 100) if max_value > 0 else 0

    html = f"""
    <div style="margin-bottom: 10px;">
        {f'<div style="font-size: 14px; margin-bottom: 4px;">{label}</div>' if label else ''}
        <div style="
            width: 100%;
            background-color: #e9ecef;
            border-radius: 8px;
            height: 24px;
            position: relative;
            overflow: hidden;
        ">
            <div style="
                width: {percentage}%;
                background-color: {color};
                height: 100%;
                border-radius: 8px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: white;
                font-weight: 600;
                font-size: 12px;
                transition: width 0.3s ease;
            ">
                {percentage:.1f}%
            </div>
        </div>
    </div>
    """

    st.markdown(html, unsafe_allow_html=True)
