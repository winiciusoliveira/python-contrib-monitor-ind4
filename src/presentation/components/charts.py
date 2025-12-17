import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import streamlit as st
from typing import List, Dict, Any


def render_bar_chart(data: pd.DataFrame, x: str, y: str, title: str, color: str = None):
    """
    Renderiza gráfico de barras

    Args:
        data: DataFrame com os dados
        x: Coluna para eixo X
        y: Coluna para eixo Y
        title: Título do gráfico
        color: Coluna para cor (opcional)
    """
    fig = px.bar(
        data,
        x=x,
        y=y,
        title=title,
        color=color,
        color_discrete_sequence=px.colors.qualitative.Set2
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="sans-serif"),
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def render_pie_chart(data: pd.DataFrame, values: str, names: str, title: str):
    """
    Renderiza gráfico de pizza

    Args:
        data: DataFrame com os dados
        values: Coluna com valores
        names: Coluna com nomes
        title: Título do gráfico
    """
    fig = px.pie(
        data,
        values=values,
        names=names,
        title=title,
        color_discrete_sequence=px.colors.qualitative.Pastel
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="sans-serif"),
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def render_timeline_chart(data: List[Dict[str, Any]], title: str = "Timeline"):
    """
    Renderiza gráfico de timeline (Gantt)

    Args:
        data: Lista de dicionários com {Task, Start, Finish, Resource}
        title: Título do gráfico
    """
    if not data:
        st.info("Sem dados para exibir no timeline")
        return

    df = pd.DataFrame(data)

    fig = px.timeline(
        df,
        x_start="Start",
        x_end="Finish",
        y="Task",
        color="Resource",
        title=title
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="sans-serif"),
        height=500,
        xaxis_title="Tempo",
        yaxis_title="Máquina"
    )

    st.plotly_chart(fig, use_container_width=True)


def render_heatmap(data: pd.DataFrame, x: str, y: str, values: str, title: str):
    """
    Renderiza heatmap

    Args:
        data: DataFrame com os dados
        x: Coluna para eixo X
        y: Coluna para eixo Y
        values: Coluna com valores
        title: Título do gráfico
    """
    pivot = data.pivot(index=y, columns=x, values=values)

    fig = go.Figure(data=go.Heatmap(
        z=pivot.values,
        x=pivot.columns,
        y=pivot.index,
        colorscale='RdYlGn_r',  # Vermelho = ruim, Verde = bom
        text=pivot.values,
        texttemplate='%{text:.1f}',
        textfont={"size": 10}
    ))

    fig.update_layout(
        title=title,
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="sans-serif"),
        height=500,
        xaxis_title=x,
        yaxis_title=y
    )

    st.plotly_chart(fig, use_container_width=True)


def render_line_chart(data: pd.DataFrame, x: str, y: str, title: str, group_by: str = None):
    """
    Renderiza gráfico de linha

    Args:
        data: DataFrame com os dados
        x: Coluna para eixo X
        y: Coluna para eixo Y
        title: Título do gráfico
        group_by: Coluna para agrupar (múltiplas linhas)
    """
    fig = px.line(
        data,
        x=x,
        y=y,
        title=title,
        color=group_by,
        markers=True
    )

    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="sans-serif"),
        height=400
    )

    st.plotly_chart(fig, use_container_width=True)


def render_pareto_chart(data: pd.DataFrame, category: str, value: str, title: str):
    """
    Renderiza gráfico de Pareto (barras + linha acumulada)

    Args:
        data: DataFrame com os dados
        category: Coluna de categorias
        value: Coluna de valores
        title: Título do gráfico
    """
    # Ordena por valor decrescente
    df_sorted = data.sort_values(by=value, ascending=False).copy()

    # Calcula percentual acumulado
    df_sorted['cumulative_pct'] = (df_sorted[value].cumsum() / df_sorted[value].sum() * 100)

    # Cria figura com eixos duplos
    fig = go.Figure()

    # Barras
    fig.add_trace(go.Bar(
        x=df_sorted[category],
        y=df_sorted[value],
        name='Quantidade',
        marker_color='#1f77b4'
    ))

    # Linha acumulada
    fig.add_trace(go.Scatter(
        x=df_sorted[category],
        y=df_sorted['cumulative_pct'],
        name='% Acumulado',
        yaxis='y2',
        mode='lines+markers',
        marker_color='#ff7f0e',
        line=dict(width=3)
    ))

    # Layout com eixo duplo
    fig.update_layout(
        title=title,
        xaxis=dict(title=category),
        yaxis=dict(title='Quantidade', side='left'),
        yaxis2=dict(title='% Acumulado', side='right', overlaying='y', range=[0, 100]),
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(family="sans-serif"),
        height=400,
        legend=dict(x=0.7, y=1.1, orientation='h')
    )

    st.plotly_chart(fig, use_container_width=True)
