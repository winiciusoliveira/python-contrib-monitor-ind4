# Guia de Migração - v1.0 → v2.0

## 📋 Visão Geral

Este guia ajuda na transição do sistema antigo (monolítico) para a nova arquitetura (Clean Architecture).

## 🔄 Mudanças Principais

### Arquivos Novos vs Antigos

| Antigo | Novo | Status |
|--------|------|--------|
| `service_monitor.py` | `service_monitor_v2.py` | ✅ Refatorado |
| `dashboard.py` | `dashboard_v2.py` | ✅ Refatorado |
| `database.py` | `src/infrastructure/database/` | ✅ Modularizado |
| `opc_utils.py` | `src/infrastructure/communication/opc_client.py` | ✅ Refatorado |
| `network_utils.py` | `src/infrastructure/communication/network_client.py` | ✅ Refatorado |
| - | `src/domain/` | ✨ Novo |
| - | `src/application/` | ✨ Novo |
| - | `src/presentation/` | ✨ Novo |

### Mantidos (sem alterações)

- ✅ `config.json` - Configuração de máquinas
- ✅ `opc_config.py` - Mapeamento OPC (usado temporariamente)
- ✅ `notifications.py` - Notificações Teams
- ✅ `integration_api.py` - API externa
- ✅ `monitoramento.db` - Banco de dados

## 🚀 Passo a Passo da Migração

### Opção 1: Usar Nova Versão Lado a Lado (Recomendado)

Esta opção permite testar a nova versão sem afetar a antiga:

1. **Pare os serviços antigos**:
   - Feche `service_monitor.py`
   - Feche `dashboard.py`

2. **Inicie os novos serviços**:
   ```bash
   # Terminal 1: Serviço de monitoramento
   python service_monitor_v2.py

   # Terminal 2: Dashboard
   streamlit run dashboard_v2.py
   ```

3. **Teste por 1-2 dias**:
   - Verifique se todos os dados estão corretos
   - Compare com a versão antiga se necessário

4. **Commit da migração**:
   - Se tudo estiver OK, renomeie os arquivos:
   ```bash
   # Backup do antigo
   mv service_monitor.py service_monitor_v1_backup.py
   mv dashboard.py dashboard_v1_backup.py

   # Promove a nova versão
   mv service_monitor_v2.py service_monitor.py
   mv dashboard_v2.py dashboard.py
   ```

### Opção 2: Migração Direta

Se preferir migrar diretamente:

1. **Backup completo**:
   ```bash
   # Faça backup de todo o diretório
   cp -r python-contrib-monitor-ind4 python-contrib-monitor-ind4_backup
   ```

2. **Substitua os arquivos**:
   ```bash
   mv service_monitor.py service_monitor_old.py
   mv dashboard.py dashboard_old.py
   mv service_monitor_v2.py service_monitor.py
   mv dashboard_v2.py dashboard.py
   ```

3. **Teste imediatamente**:
   - Inicie o sistema
   - Verifique todos os recursos

## 🔧 Compatibilidade

### Banco de Dados

✅ **Totalmente Compatível**

A nova versão usa o mesmo schema do banco:
- `historico_paradas`
- `eventos`
- Nova tabela `metricas_diarias` (criada automaticamente)

### Configuração

✅ **Totalmente Compatível**

O `config.json` continua com o mesmo formato:

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

### Estado Persistente

✅ **Totalmente Compatível**

O `estado_atual.json` mantém o mesmo formato, apenas com metadados adicionais:

```json
{
  "metadata": {
    "ultimo_sinal": "2024-12-16 14:30:00",
    "status_servico": "RODANDO",
    "versao": "2.0 (Clean Architecture)"
  },
  "maquinas": { ... }
}
```

## 📊 Novos Recursos Disponíveis

Após migração, você terá acesso a:

### Dashboard

1. **5 Abas Organizadas**:
   - Visão Geral (KPIs + Status)
   - Detalhes (Cards + Tabela)
   - Análise Temporal (Pareto + Turnos)
   - Histórico (Filtros + Export)
   - Configuração (Diagnóstico)

2. **Gráficos Interativos**:
   - Pareto de paradas
   - Pizza de distribuição
   - Barras de turnos
   - Heatmaps (futuro)

3. **Análises Avançadas**:
   - Máquinas inativas hoje
   - Top offenders
   - KPIs por período

### Backend

1. **Arquitetura Modular**:
   - Fácil adicionar novos protocolos
   - Testável
   - Manutenível

2. **Serviços Especializados**:
   - `MonitorService` - Monitoramento
   - `AnalyticsService` - Análises
   - Repositórios separados

## ⚠️ Possíveis Problemas

### 1. Import Errors

**Problema**: `ModuleNotFoundError: No module named 'src'`

**Solução**: O Python está executando do diretório errado

```bash
cd C:\Users\Ind4.0\PycharmProjects\python-contrib-monitor-ind4
python service_monitor_v2.py
```

### 2. Conexões OPC Antigas

**Problema**: Conexões OPC da versão antiga ainda abertas

**Solução**: Reinicie o computador ou mate os processos Python:

```bash
# Windows
taskkill /F /IM python.exe

# Depois reinicie apenas o novo
python service_monitor_v2.py
```

### 3. Porta do Streamlit Ocupada

**Problema**: `Address already in use`

**Solução**: Feche o dashboard antigo ou use outra porta:

```bash
streamlit run dashboard_v2.py --server.port 8502
```

## 📝 Checklist de Migração

- [ ] Backup completo do sistema antigo
- [ ] Testar `service_monitor_v2.py` (pelo menos 1h)
- [ ] Verificar dashboard `dashboard_v2.py`
- [ ] Confirmar que dados aparecem corretamente
- [ ] Testar filtros (Unidade/Planta/Setor)
- [ ] Verificar histórico de paradas
- [ ] Testar export CSV
- [ ] Verificar notificações Teams
- [ ] Validar KPIs (Disponibilidade, MTBF, MTTR)
- [ ] Testar análise de Pareto
- [ ] Confirmar período de análise variável
- [ ] Documentar qualquer problema encontrado

## 🆘 Rollback (Se Necessário)

Se algo der errado, volte para a versão antiga:

```bash
# Pare os novos serviços (Ctrl+C em ambos terminais)

# Volte para os arquivos antigos
python service_monitor.py
streamlit run dashboard.py
```

Seus dados não serão perdidos pois o banco é compatível.

## 📞 Suporte

Se encontrar problemas:

1. Verifique os logs no terminal
2. Consulte o `README_V2.md`
3. Verifique as mensagens de erro
4. Documente o problema para correção

## 🎉 Próximos Passos Após Migração

1. **Familiarize-se com as novas abas**
2. **Configure alertas personalizados** (se necessário)
3. **Explore os gráficos de Pareto** para identificar gargalos
4. **Use a análise temporal** para decisões estratégicas
5. **Exporte relatórios CSV** para análises externas

## 💡 Dicas

- Mantenha ambas versões por 1 semana para comparação
- Use os filtros da sidebar para focar em setores específicos
- Altere o período de análise para ver tendências
- Export CSV regularmente para histórico externo
- Monitore o "Tempo de scan" no terminal (deve ser < 5s)
