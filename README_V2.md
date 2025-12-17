# Sistema de Monitoramento Industrial 4.0 - v2.0

## 🎯 Visão Geral

Sistema modernizado de monitoramento industrial com arquitetura limpa, dashboard otimizado e análises avançadas.

## 🏗️ Arquitetura

### Clean Architecture + DDD

```
📁 src/
├── 📁 domain/              # Regras de Negócio (independente de frameworks)
│   ├── models.py           # Entidades: Machine, Downtime, Event, KPIData
│   ├── enums.py            # Enumerações: MachineStatus, CommunicationType, Turno
│   └── interfaces.py       # Contratos/Interfaces
│
├── 📁 application/         # Casos de Uso e Serviços
│   ├── services/
│   │   ├── monitor_service.py        # Lógica de monitoramento
│   │   └── analytics_service.py      # Cálculos de KPIs
│   └── dtos.py             # Data Transfer Objects
│
├── 📁 infrastructure/      # Implementações Técnicas
│   ├── database/
│   │   ├── connection.py              # Conexão SQLite
│   │   └── repositories.py            # CRUD (Machine, Downtime, Event)
│   └── communication/
│       ├── opc_client.py              # Cliente OPC UA
│       └── network_client.py          # Cliente de rede (ping)
│
└── 📁 presentation/        # Interface UI
    ├── pages/              # Páginas do dashboard (futuro)
    └── components/
        ├── metrics_card.py            # Cards de métricas
        ├── machine_card.py            # Cards de máquinas
        └── charts.py                  # Gráficos (Plotly)
```

## ✨ Principais Melhorias

### 1. Dashboard Moderno com 5 Abas

#### 📊 Aba 1: Visão Geral
- KPIs principais (Total, Produzindo, Paradas, Críticas, Disponibilidade)
- Distribuição de status (gráfico pizza)
- Disponibilidade por setor (barras de progresso)
- Top máquinas inativas do dia

#### 🔍 Aba 2: Detalhes por Hierarquia
- Visualização em Cards ou Tabela
- Filtros por Unidade/Planta/Setor
- Informações completas de cada máquina

#### 📈 Aba 3: Análise Temporal
- Gráfico de Pareto (Top 10 com mais paradas)
- Distribuição por turno
- Análise de tendências

#### 📜 Aba 4: Histórico de Paradas
- Tabela completa de paradas
- Filtros por equipamento e duração
- Export para CSV
- Estatísticas detalhadas

#### ⚙️ Aba 5: Configuração e Controle
- Informações do sistema
- Testes de conectividade (em desenvolvimento)
- Logs do sistema (em desenvolvimento)

### 2. KPIs Industriais

- **Disponibilidade**: (Tempo Produzindo / Tempo Total) × 100
- **MTBF**: Mean Time Between Failures (tempo médio entre falhas)
- **MTTR**: Mean Time To Repair (tempo médio de reparo)
- **OEE**: Overall Equipment Effectiveness (futuro)

### 3. Análises Avançadas

- Identificação rápida de máquinas inativas
- Análise de Pareto (regra 80/20)
- Distribuição por turnos
- Timeline de eventos

### 4. Código Limpo e Extensível

- **Separation of Concerns**: Cada camada tem responsabilidade única
- **Dependency Inversion**: Interfaces permitem trocar implementações
- **Strategy Pattern**: Fácil adicionar novos protocolos (Modbus, MQTT, etc.)
- **Repository Pattern**: Acesso a dados abstraído
- **DRY**: Componentes reutilizáveis

## 🚀 Como Usar

### Iniciar o Sistema (Novo)

1. **Iniciar Serviço de Monitoramento**:
   ```bash
   python service_monitor_v2.py
   ```

2. **Iniciar Dashboard**:
   ```bash
   streamlit run dashboard_v2.py
   ```

### Migração do Sistema Antigo

Os arquivos `v2` são a nova versão. Os arquivos antigos foram mantidos para compatibilidade:

- `service_monitor.py` → `service_monitor_v2.py` (novo)
- `dashboard.py` → `dashboard_v2.py` (novo)

## 📊 Novos Recursos

### 1. Análise de Inatividade

```python
# Identifica máquinas paradas >= 30 min hoje
analytics_service.get_inactive_machines_today(threshold_minutes=30)
```

### 2. Top Offenders (Pareto)

```python
# Retorna top 10 máquinas com mais paradas
analytics_service.get_top_offenders(limit=10)
```

### 3. KPIs por Período

```python
# Calcula KPIs de um equipamento
kpis = analytics_service.calculate_kpis(
    equipamento="Tear#01",
    data_inicio=datetime(2024, 1, 1),
    data_fim=datetime.now()
)
```

### 4. Distribuição por Turno

```python
# Tempo de paradas por turno
tempo_turno = analytics_service.get_downtime_by_turno(
    data_inicio, data_fim
)
```

## 🔧 Extensibilidade

### Adicionar Novo Protocolo de Comunicação

1. Criar classe que implementa `ICommunicationProtocol`:

```python
from src.domain.interfaces import ICommunicationProtocol

class ModbusTCPClient(ICommunicationProtocol):
    def read_value(self, machine, tag):
        # Implementação Modbus
        pass

    def write_value(self, machine, tag, value):
        # Implementação Modbus
        pass

    def check_connection(self, machine):
        # Implementação Modbus
        pass
```

2. Registrar no `service_monitor_v2.py`:

```python
modbus_client = ModbusTCPClient()
communication_protocols = {
    CommunicationType.OPC_UA.value: opc_client,
    CommunicationType.MODBUS_TCP.value: modbus_client,
    # ...
}
```

### Adicionar Nova Análise

Estender `AnalyticsService`:

```python
class AnalyticsService:
    def nova_analise_customizada(self, params):
        # Implementação
        pass
```

## 📦 Dependências

Não foram adicionadas novas dependências. O sistema usa:

- streamlit
- pandas
- plotly
- opcua (python-opcua)
- sqlite3 (built-in)

## 🎨 Componentes Reutilizáveis

### Métricas

```python
from src.presentation.components.metrics_card import render_kpi_row

render_kpi_row({
    'Total': 100,
    'Ativas': 85,
    'Inativas': 15
})
```

### Cards de Máquina

```python
from src.presentation.components.machine_card import render_machine_card

render_machine_card(
    nome="Tear#01",
    status="PRODUZINDO",
    desde="14:30:00",
    setor="Tecelagem",
    ip="10.243.67.30"
)
```

### Gráficos

```python
from src.presentation.components.charts import render_pareto_chart

render_pareto_chart(df, 'equipamento', 'total_paradas', 'Top Offenders')
```

## 📈 Roadmap Futuro

- [ ] Escrita de tags OPC (controle remoto)
- [ ] Integração com Modbus TCP
- [ ] MQTT para IoT
- [ ] Machine Learning para previsão de falhas
- [ ] Alertas por email
- [ ] API REST para integração
- [ ] App Mobile
- [ ] Performance: Calcular OEE real

## 🤝 Contribuindo

O código está organizado para facilitar contribuições:

1. **Domain**: Adicione novas entidades ou enums
2. **Application**: Adicione novos casos de uso
3. **Infrastructure**: Adicione novas implementações de protocolos
4. **Presentation**: Adicione novos componentes ou páginas

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
- Extensibilidade
- Testabilidade
- Performance (cache de conexões OPC)
- UX do dashboard

#### Mantido
- Compatibilidade com config.json
- Integração com API externa
- Notificações Teams
- Banco SQLite
