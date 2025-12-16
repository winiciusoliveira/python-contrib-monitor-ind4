import streamlit as st
import requests
import toml
import os
from datetime import datetime

SECRETS_PATH = ".streamlit/secrets.toml"

def get_config_keys() :
	"""Lê configurações e múltiplos webhooks do Teams"""
	conf = { "tg_token" : None, "tg_chat" : None, "teams_webhooks" : { } }
	
	if os.path.exists(SECRETS_PATH) :
		try :
			with open(SECRETS_PATH, "r") as f :
				data = toml.load(f)
				if "telegram" in data :
					conf["tg_token"] = data["telegram"].get("token")
					conf["tg_chat"] = data["telegram"].get("chat_id")
				# Lê dicionário de webhooks do Teams
				if "teams" in data :
					# Espera estrutura: [teams] geral="url", manutencao="url"
					conf["teams_webhooks"] = data["teams"]
		except Exception as e :
			print(f"⚠️ Erro secrets: {e}")
	
	# Fallback para st.secrets (Cloud)
	try :
		if not conf["tg_token"] :
			conf["tg_token"] = st.secrets["telegram"]["token"]
			conf["tg_chat"] = st.secrets["telegram"]["chat_id"]
		if not conf["teams_webhooks"] :
			conf["teams_webhooks"] = st.secrets["teams"]
	except :
		pass
	
	return conf

def _enviar_telegram(token, chat_id, mensagem) :
	if not token or not chat_id : return
	try :
		url = f"https://api.telegram.org/bot{token}/sendMessage"
		payload = { "chat_id" : chat_id, "text" : mensagem, "parse_mode" : "Markdown" }
		requests.post(url, json=payload, timeout=5)
	except Exception as e :
		print(f"❌ Erro Telegram: {e}")

def _enviar_teams(webhook_url, mensagem, cor="Accent") :
	if not webhook_url : return
	try :
		payload = {
			"type" : "message", "attachments" : [
				{
					"contentType" : "application/vnd.microsoft.card.adaptive", "content" : {
					"$schema" : "http://adaptivecards.io/schemas/adaptive-card.json", "type" : "AdaptiveCard", "version" : "1.4", "msteams" : { "width" : "Full" }, "body" : [
						{ "type" : "TextBlock", "text" : "🏭 Alerta Industrial", "weight" : "Bolder", "size" : "Medium", "color" : cor },
						{ "type" : "TextBlock", "text" : mensagem.replace("\n", "\n\n"), "wrap" : True },
						{ "type" : "TextBlock", "text" : f"📅 {datetime.now().strftime('%d/%m %H:%M')}", "size" : "Small", "isSubtle" : True }
					]
				}
				}
			]
		}
		requests.post(webhook_url, json=payload, headers={ 'Content-Type' : 'application/json' }, timeout=10)
	except Exception as e :
		print(f"❌ Erro Teams: {e}")

def enviar_notificacao_inteligente(mensagem, motivo, duracao_minutos) :
	"""
	Lógica Central de Roteamento
	"""
	config = get_config_keys()
	
	# 1. TELEGRAM: Apenas se parou por mais de 2 minutos (configurável)
	if duracao_minutos >= 2 :
		_enviar_telegram(config["tg_token"], config["tg_chat"], mensagem)
	
	# 2. TEAMS: Roteamento por tópico
	webhooks = config["teams_webhooks"]
	
	# Normaliza motivo para busca
	motivo_upper = motivo.upper()
	
	# Define canal alvo (default é 'geral' ou o primeiro que achar)
	target_url = webhooks.get("geral") or next(iter(webhooks.values()), None)
	
	# Regras de Negócio
	if "ELÉTRICA" in motivo_upper or "ELETRICA" in motivo_upper :
		target_url = webhooks.get("eletrica", target_url)
	elif "MECÂNICA" in motivo_upper or "MANUTENÇÃO" in motivo_upper :
		target_url = webhooks.get("manutencao", target_url)
	
	if target_url :
		_enviar_teams(target_url, mensagem, cor="Attention" if "PARADA" in motivo_upper else "Accent")
