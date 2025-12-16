import streamlit as st
import pandas as pd
import plotly.express as px
from streamlit_autorefresh import st_autorefresh
import database

st.set_page_config(page_title="Monitoramento 4.0", layout="wide", page_icon="🏭")
st_autorefresh(interval=3000, key="ui_update")

# --- CONTROLE DE TEMA E CSS (CORRIGIDO E BLINDADO) ---
with st.sidebar :
	st.header("⚙️ Visualização")
	tema = st.radio("Tema:", ["Claro ☀️", "Escuro 🌙"], index=1)
	
	# 1. CSS Base (Comum aos dois temas)
	css_rules = """
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    .block-container {padding-top: 1rem; padding-bottom: 3rem;}
    """
	
	# 2. Adiciona regras específicas do tema
	if tema == "Escuro 🌙" :
		css_rules += """
        .stApp { background-color: #0e1117; color: white; }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #262730 !important;
            border: 1px solid #41444d !important;
            border-radius: 8px;
            padding: 15px;
        }

        [data-testid="stMetricLabel"] { color: #a3a8b8 !important; }
        [data-testid="stMetricValue"] { color: #ffffff !important; }
        """
	else :
		# Modo Claro (Shadow Design)
		css_rules += """
        .stApp { background-color: #f0f2f6; color: black; }

        [data-testid="stVerticalBlockBorderWrapper"] {
            background-color: #ffffff !important;
            border: 1px solid #cccccc !important;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1) !important;
            border-radius: 8px;
            padding: 15px;
        }

        h1, h2, h3, h4, h5, h6, p, div { color: #31333F; }

        [data-testid="stMetricLabel"] { color: #666666 !important; }
        [data-testid="stMetricValue"] { color: #000000 !important; }
        """
	
	# 3. Injeta tudo de uma vez sem indentação perigosa
	st.markdown(f"<style>{css_rules}</style>", unsafe_allow_html=True)

st.title("🏭 Monitoramento Industrial")

# --- 1. CARGA DE DADOS ---
conteudo_json = database.carregar_estado_persistente()

if not conteudo_json :
	st.info("⏳ Aguardando serviço de backend...")
	st.stop()

dados_dict = conteudo_json.get("maquinas", { })

lista_dados = []
for nome, info in dados_dict.items() :
	if not isinstance(info, dict) : continue
	
	status = info.get('status', 'Unknown')
	status_curto = status.split("|")[0].strip() if "|" in status else status
	
	if info.get('contador', 0) > 0 and "SEM REDE" not in status :
		status = f"⚠️ Instável ({info['contador']})"
	
	lista_dados.append({
		"Máquina" : nome,
		"IP" : info.get('ip', '-'),
		"Status" : status,
		"StatusCurto" : status_curto,
		"Desde" : info.get('desde', '-').split(' ')[1] if ' ' in info.get('desde', '-') else '-',
		"Cor" : info.get('cor', '#808080'),
		"Unidade" : info.get('unidade', 'Geral'),
		"Planta" : info.get('planta', 'Geral'),
		"Setor" : info.get('setor', 'Geral')
	})

df = pd.DataFrame(lista_dados)
if df.empty :
	st.warning("Nenhuma máquina encontrada.")
	st.stop()

df = df.sort_values(by="Máquina").reset_index(drop=True)

# --- 2. FILTROS ---
with st.sidebar :
	st.divider()
	st.header("🔍 Filtros")
	
	opt_unidade = sorted(list(df['Unidade'].unique()))
	sel_unidade = st.multiselect("Unidade:", options=opt_unidade, default=opt_unidade)
	df_step1 = df[df['Unidade'].isin(sel_unidade)]
	
	opt_planta = sorted(list(df_step1['Planta'].unique()))
	sel_planta = st.multiselect("Planta:", options=opt_planta, default=opt_planta)
	df_step2 = df_step1[df_step1['Planta'].isin(sel_planta)]
	
	opt_setor = sorted(list(df_step2['Setor'].unique()))
	sel_setor = st.multiselect("Setor:", options=opt_setor, default=opt_setor)
	
	st.divider()
	filtro_status = st.multiselect("Status Específico:", options=df['Status'].unique())
	modo_view = st.radio("Modo:", ["📱 Cards (Celular)", "🖥️ Tabela (PC)"])
	
	if st.button("🔄 Atualizar") :
		st.rerun()

df_view = df_step2[df_step2['Setor'].isin(sel_setor)]
if filtro_status :
	df_view = df_view[df_view['Status'].isin(filtro_status)]

# --- 3. MÉTRICAS ---
c1, c2, c3, c4 = st.columns(4)
with c1 :
	with st.container(border=True) :
		st.metric("Total", len(df_view))
with c2 :
	with st.container(border=True) :
		st.metric("Produzindo", len(df_view[df_view['Status'].str.contains("PRODUZINDO", case=False, na=False)]))
with c3 :
	with st.container(border=True) :
		st.metric("Parada", len(df_view[df_view['Status'].str.contains("PARADA", case=False, na=False)]))
with c4 :
	with st.container(border=True) :
		st.metric("Crítico", len(df_view[df_view['Status'].str.contains("SEM REDE|FALHA", case=False, na=False)]))

st.divider()

# --- 4. VISUALIZAÇÃO PRINCIPAL ---
if modo_view == "📱 Cards (Celular)" :
	if df_view.empty :
		st.info("Nenhum dado com os filtros atuais.")
	else :
		cols = st.columns(2)
		for index, row in df_view.iterrows() :
			col_idx = index % 2
			with cols[col_idx] :
				with st.container(border=True) :
					icon = "⚪"
					status_txt = row['Status']
					
					if "PRODUZINDO" in status_txt :
						icon = "🟢"
					elif "PARADA" in status_txt :
						icon = "🔴"
					elif "SEM REDE" in status_txt :
						icon = "🔌"
					elif "FALHA" in status_txt :
						icon = "⚠️"
					
					st.markdown(f"#### {row['Máquina']}")
					st.markdown(f"**{icon} {row['StatusCurto']}**")
					st.caption(f"⏱️ {row['Desde']} | 📍 {row['Setor']}")

else :
	# Modo Tabela
	st.dataframe(df_view, width='stretch', height=600, column_config={
		"Máquina" : st.column_config.TextColumn("Equipamento", width="small"), "Status" : st.column_config.TextColumn("Status Atual", width="medium"), "StatusCurto" : None, "Cor" : None, "Unidade" : None, "Planta" : None
	}, hide_index=True)

# --- 5. HISTÓRICO ---
st.divider()
st.subheader("📜 Histórico de Paradas")
try :
	df_hist = database.get_top_offenders(limit=10)
	if not df_hist.empty :
		st.dataframe(df_hist, use_container_width=True)
	else :
		st.caption("Sem dados históricos recentes.")
except :
	st.caption("Conectando ao banco...")