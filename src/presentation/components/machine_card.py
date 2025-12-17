import streamlit as st
from typing import Optional


def render_machine_card(
    nome: str,
    status: str,
    desde: str,
    setor: str,
    ip: Optional[str] = None,
    detalhes: Optional[dict] = None
):
    """
    Renderiza um card de máquina

    Args:
        nome: Nome da máquina
        status: Status atual
        desde: Timestamp desde quando está nesse status
        setor: Setor da máquina
        ip: Endereço IP (opcional)
        detalhes: Detalhes adicionais (opcional)
    """
    # Mapeia status para ícones
    icon_map = {
        'PRODUZINDO': '🟢',
        'PARADA': '🔴',
        'SEM REDE': '🔌',
        'FALHA OPC': '⚠️',
        'ERRO LEITURA': '❌',
        'DESCONHECIDO': '⚪'
    }

    # Encontra ícone
    icon = '⚪'
    for key, value in icon_map.items():
        if key in status.upper():
            icon = value
            break

    with st.container(border=True):
        st.markdown(f"#### {nome}")
        st.markdown(f"**{icon} {status}**")

        info_parts = [f"⏱️ {desde}", f"📍 {setor}"]
        if ip:
            info_parts.append(f"🌐 {ip}")

        st.caption(" | ".join(info_parts))

        # Detalhes adicionais (expansível)
        if detalhes:
            with st.expander("Ver detalhes"):
                for key, value in detalhes.items():
                    st.text(f"{key}: {value}")


def render_machine_list_compact(maquinas: list):
    """
    Renderiza lista compacta de máquinas (formato tabular)

    Args:
        maquinas: Lista de dicionários com dados das máquinas
    """
    for maq in maquinas:
        icon_map = {
            'PRODUZINDO': '🟢',
            'PARADA': '🔴',
            'SEM REDE': '🔌',
            'FALHA OPC': '⚠️'
        }

        icon = '⚪'
        status = maq.get('status', '')
        for key, value in icon_map.items():
            if key in status.upper():
                icon = value
                break

        col1, col2, col3 = st.columns([2, 3, 1])

        with col1:
            st.markdown(f"**{maq.get('nome', 'N/A')}**")
        with col2:
            st.markdown(f"{icon} {status}")
        with col3:
            st.caption(maq.get('desde', ''))

        st.divider()


def render_machine_timeline(nome: str, periodos: list):
    """
    Renderiza timeline de uma máquina (Gantt simplificado)

    Args:
        nome: Nome da máquina
        periodos: Lista de períodos com {inicio, fim, status, cor}
    """
    st.markdown(f"**{nome}**")

    # Timeline horizontal usando HTML/CSS
    html_parts = ['<div style="display: flex; height: 30px; border-radius: 4px; overflow: hidden;">']

    for periodo in periodos:
        cor = periodo.get('cor', '#808080')
        duracao_pct = periodo.get('duracao_pct', 10)  # Percentual de duração
        titulo = periodo.get('titulo', '')

        html_parts.append(f'''
            <div style="
                background-color: {cor};
                width: {duracao_pct}%;
                height: 100%;
                border-right: 1px solid white;
            " title="{titulo}"></div>
        ''')

    html_parts.append('</div>')

    st.markdown(''.join(html_parts), unsafe_allow_html=True)
    st.caption(f"Timeline do dia")
