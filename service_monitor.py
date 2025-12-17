import time
from datetime import datetime
import sys
import os

# Adiciona o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Importações da nova arquitetura
from src.infrastructure.database.connection import DatabaseConnection
from src.infrastructure.database.repositories import MachineRepository, DowntimeRepository, EventRepository
from src.infrastructure.communication.opc_client import OPCUAClient
from src.infrastructure.communication.network_client import NetworkClient
from src.application.services.monitor_service import MonitorService
from src.domain.enums import CommunicationType

# Importações legadas (enquanto não refatoramos tudo)
import notifications
import integration_api


# ============== CONFIGURAÇÃO ==============
INTERVALO_SCAN = 5  # segundos
LIMITE_FALHAS = 3
TEMPO_ESTABILIDADE = 60  # segundos


def carregar_node_ids_opc():
    """
    Carrega mapeamento de node_ids do OPC a partir do config antigo
    """
    import opc_config

    return opc_config.OPC_MAP


def atualizar_config_com_node_ids(machine_repo: MachineRepository):
    """
    Atualiza configuração das máquinas com node_ids do OPC
    """
    node_map = carregar_node_ids_opc()

    for api_id, opc_data in node_map.items():
        machine = machine_repo.get_by_id(api_id)
        if machine:
            machine.comunicacao.node_id = opc_data.get('node_running')
            machine.comunicacao.endpoint = opc_data.get('endpoint')


def loop_principal():
    """Loop principal de monitoramento"""
    print(f"🚀 Serviço de Monitoramento v2.0 - {datetime.now()}")
    print("📦 Arquitetura: Clean Architecture + DDD")

    # Inicializa infraestrutura
    db = DatabaseConnection()
    db.init_schema()
    print("✅ Banco de dados inicializado")

    # Inicializa repositórios
    machine_repo = MachineRepository()
    downtime_repo = DowntimeRepository(db)
    event_repo = EventRepository(db)

    # Atualiza configuração com node_ids OPC
    atualizar_config_com_node_ids(machine_repo)
    print("✅ Configurações OPC carregadas")

    # Inicializa protocolos de comunicação
    opc_client = OPCUAClient(timeout=2)
    network_client = NetworkClient(timeout=1)

    communication_protocols = {
        CommunicationType.OPC_UA.value: opc_client,
        CommunicationType.NETWORK_PING.value: network_client
    }

    # Inicializa serviço de monitoramento
    monitor_service = MonitorService(
        machine_repo=machine_repo,
        downtime_repo=downtime_repo,
        event_repo=event_repo,
        communication_protocols=communication_protocols,
        limite_falhas=LIMITE_FALHAS,
        tempo_estabilidade=TEMPO_ESTABILIDADE
    )

    print(f"✅ Monitorando {len(machine_repo.get_all())} máquinas")
    print("=" * 60)

    # Notifica início
    try:
        notifications.enviar_notificacao_inteligente(
            "🚀 Sistema de Monitoramento v2.0 Iniciado",
            "SISTEMA",
            0
        )
    except:
        print("⚠️ Notificações não disponíveis")

    primeira_execucao = True
    contador_scan = 0

    while True:
        inicio_scan = time.time()
        contador_scan += 1

        try:
            print(f"\n🔍 Scan #{contador_scan} - {datetime.now().strftime('%H:%M:%S')}")

            # Busca dados da API externa (se disponível)
            dados_api = {}
            try:
                dados_api = integration_api.fetch_metris_status()
                print(f"   ✅ API Externa: {len(dados_api)} registros")
            except Exception as e:
                print(f"   ⚠️ API Externa indisponível: {e}")

            # Atualiza descrições de status das máquinas com dados da API
            for machine in machine_repo.get_all():
                if machine.api_id in dados_api:
                    api_info = dados_api[machine.api_id]
                    machine.status_descricao = api_info.get('descricao', '')
                    machine.cor = api_info.get('cor', machine.cor)

            # Executa scan de todas as máquinas
            maquinas_atualizadas = monitor_service.scan_machines()

            # Estatísticas do scan
            stats = monitor_service.get_dashboard_metrics()

            print(f"   📊 Status: "
                  f"{stats['maquinas_produzindo']} Prod | "
                  f"{stats['maquinas_paradas']} Paradas | "
                  f"{stats['maquinas_criticas']} Críticas")

            print(f"   📈 Disponibilidade: {stats['disponibilidade_geral']:.1f}%")

            # Salva estado
            machine_repo.save_state()

            if primeira_execucao:
                print("   💾 Estado inicial salvo")
                primeira_execucao = False

        except Exception as e:
            print(f"   ❌ Erro no scan: {e}")
            import traceback
            traceback.print_exc()

        # Controle de tempo
        tempo_gasto = time.time() - inicio_scan
        print(f"   ⏱️ Tempo de scan: {tempo_gasto:.2f}s")

        # Sleep ajustado
        sleep_time = max(0.0, INTERVALO_SCAN - tempo_gasto)
        if sleep_time > 0:
            time.sleep(sleep_time)


if __name__ == "__main__":
    try:
        loop_principal()
    except KeyboardInterrupt:
        print("\n\n🛑 Serviço interrompido pelo usuário")
    except Exception as e:
        print(f"\n\n❌ Erro fatal: {e}")
        import traceback
        traceback.print_exc()
