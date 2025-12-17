# 🏭 Sistema de Monitoramento Industrial 4.0 - v2.0

Sistema modernizado de monitoramento industrial com **Clean Architecture**, dashboard otimizado com 5 abas e análises avançadas.

## ✨ O Que Mudou?

### Versão 2.0 (ATUAL)
- ✅ **Arquitetura Clean** (Domain, Application, Infrastructure, Presentation)
- ✅ **Dashboard com 5 abas** organizadas
- ✅ **KPIs industriais** (Disponibilidade, MTBF, MTTR)
- ✅ **Gráficos interativos** (Pareto, Pizza, Barras)
- ✅ **Análises avançadas** (Inatividade, Top Offenders, Turnos)
- ✅ **Export para CSV**
- ✅ **Código modular e extensível**

### Versão 1.0 (Backup em `backup_v1/`)
- Dashboard simples (1 tela)
- Código monolítico
- KPIs básicos

---

## 🚀 Como Usar

### Opção 1: Arquivo Batch (Mais Fácil)

Duplo clique em:
```
INICIAR_TUDO.bat
```

Isso vai:
1. Ativar o ambiente virtual
2. Iniciar o serviço de monitoramento
3. Iniciar o dashboard
4. Abrir o navegador automaticamente

### Opção 2: Manual

```bash
# Terminal 1: Serviço de monitoramento
python service_monitor.py

# Terminal 2: Dashboard
streamlit run dashboard.py
```

### Acessar o Dashboard

Abra o navegador em: **http://localhost:8501**

---

## 📊 Recursos do Dashboard

### 5 Abas Principais

#### 📊 Aba 1: Visão Geral
- KPIs principais (Total, Produzindo, Paradas, Críticas, Disponibilidade)
- Gráfico de distribuição de status
- Disponibilidade por setor (barras de progresso)
- **Top máquinas inativas do dia** (threshold 30 min)

#### 🔍 Aba 2: Detalhes
- Visualização em **Cards** ou **Tabela**
- Filtros por hierarquia (Unidade/Planta/Setor)
- Informações completas de cada máquina

#### 📈 Aba 3: Análise Temporal
- **Gráfico de Pareto** (Top 10 com mais paradas)
- Distribuição por turno
- Período configurável (1 a 90 dias)

#### 📜 Aba 4: Histórico
- Tabela completa de paradas
- Filtros por equipamento e duração
- **Export para CSV**

#### ⚙️ Aba 5: Configuração
- Informações do sistema
- Testes de conectividade (em desenvolvimento)
- Logs (em desenvolvimento)

### Filtros Globais (Sidebar)

- **Unidade, Planta, Setor** - Navegação por hierarquia
- **Período de Análise** - 1, 7, 15, 30 ou 90 dias

### Auto-Refresh

O dashboard atualiza automaticamente a cada 5 segundos.

---

## 📁 Estrutura do Projeto

```
python-contrib-monitor-ind4/
├── src/                      # Nova arquitetura
│   ├── domain/               # Entidades e regras de negócio
│   ├── application/          # Serviços e casos de uso
│   ├── infrastructure/       # Database e comunicação
│   └── presentation/         # Componentes UI
│
├── backup_v1/                # Backup da versão antiga
│   ├── dashboard.py
│   ├── service_monitor.py
│   └── database.py
│
├── dashboard.py              # Dashboard principal (v2.0)
├── service_monitor.py        # Serviço de monitoramento (v2.0)
├── config.json               # Configuração de máquinas
├── opc_config.py             # Mapeamento OPC
├── monitoramento.db          # Banco de dados SQLite
│
├── INICIAR_TUDO.bat          # Inicia todo o sistema
├── README.md                 # Este arquivo
├── README_V2.md              # Documentação técnica detalhada
└── MIGRATION_GUIDE.md        # Guia de migração
```

---

## 🎯 Principais Funcionalidades

### Análise de Inatividade

Identifica rapidamente quais máquinas ficaram paradas hoje:
- Threshold configurável (padrão: 30 minutos)
- Tempo total de parada
- Número de paradas
- Períodos detalhados

### KPIs Industriais

- **Disponibilidade**: (Tempo Produzindo / Tempo Total) × 100
- **MTBF**: Mean Time Between Failures (tempo médio entre falhas)
- **MTTR**: Mean Time To Repair (tempo médio de reparo)

### Análise de Pareto

Gráfico que mostra as top 10 máquinas com mais paradas (regra 80/20).

### Distribuição por Turno

Análise de paradas por:
- Turno 1: 06:00 - 14:30
- Turno 2: 14:30 - 22:52
- Turno 3: 22:52 - 06:00

---

## 🔧 Configuração

### Máquinas

Edite `config.json`:

```json
{
  "nome": "Tear#01",
  "api_id": "LOOM01",
  "ip": "10.243.67.30",
  "porta": 4840,
  "unidade": "Brasil",
  "planta": "Piracicaba",
  "setor": "Tecelagem"
}
```

### Tags OPC

Edite `opc_config.py` para configurar os node_ids das tags OPC.

---

## 📦 Dependências

- Python 3.12+
- streamlit
- pandas
- plotly
- opcua (python-opcua)
- sqlite3 (built-in)
- streamlit-autorefresh

---

## 📖 Documentação Adicional

- **README_V2.md** - Documentação técnica completa da arquitetura
- **MIGRATION_GUIDE.md** - Guia de migração da v1 para v2
- **IMPLEMENTACAO_COMPLETA.md** - Detalhes da implementação

---

## 🆘 Troubleshooting

### Dashboard não carrega dados

1. Verifique se o serviço está rodando (`service_monitor.py`)
2. Aguarde pelo menos 1 ciclo de scan (5 segundos)
3. Verifique se o arquivo `estado_atual.json` foi criado

### Erro ao importar módulos

```bash
# Certifique-se de estar no diretório correto
cd C:\Users\Ind4.0\PycharmProjects\python-contrib-monitor-ind4

# Execute a partir do diretório raiz
python service_monitor.py
streamlit run dashboard.py
```

### Conexões OPC falhando

1. Verifique a configuração em `opc_config.py`
2. Teste a conectividade de rede com as máquinas
3. Verifique se as portas OPC estão corretas

---

## 🎓 Conceitos Aplicados

- **Clean Architecture** (Robert C. Martin)
- **Domain-Driven Design** (Eric Evans)
- **SOLID Principles**
- **Repository Pattern**
- **Strategy Pattern**
- **Dependency Injection**

---

## 🚀 Próximos Passos

### Curto Prazo
- [ ] Implementar escrita de tags OPC
- [ ] Adicionar testes de conectividade na Aba 5
- [ ] Visualização de logs

### Médio Prazo
- [ ] Adicionar Modbus TCP
- [ ] Integração MQTT
- [ ] Alertas customizados

### Longo Prazo
- [ ] Machine Learning (previsão de falhas)
- [ ] API REST
- [ ] App Mobile

---

## 📝 Changelog

### v2.0.0 - 2024-12-16

#### Adicionado
- Arquitetura Clean Architecture + DDD
- Dashboard com 5 abas
- KPIs industriais (Disponibilidade, MTBF, MTTR)
- Análise de Pareto
- Análise de inatividade
- Distribuição por turnos
- Componentes reutilizáveis
- Export para CSV
- Gráficos interativos (Plotly)

#### Melhorado
- Separação de responsabilidades
- Extensibilidade (fácil adicionar novos protocolos)
- Testabilidade
- Performance (cache de conexões OPC)
- UX do dashboard

#### Mantido
- Compatibilidade com config.json
- Integração com API externa
- Notificações Teams
- Banco SQLite

---

## 🤝 Contribuindo

O código está organizado para facilitar contribuições:

1. **Domain** (`src/domain/`) - Adicione novas entidades ou enums
2. **Application** (`src/application/`) - Adicione novos casos de uso
3. **Infrastructure** (`src/infrastructure/`) - Adicione novas implementações
4. **Presentation** (`src/presentation/`) - Adicione novos componentes

---

**Desenvolvido com**: Python, Streamlit, Plotly, SQLite, OPC UA
**Arquitetura**: Clean Architecture + DDD
**Versão**: 2.0.0
**Data**: Dezembro 2024
