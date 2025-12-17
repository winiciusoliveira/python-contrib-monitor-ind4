from typing import Optional, Any, Dict
from opcua import Client, ua
import socket
from ...domain.models import Machine
from ...domain.interfaces import ICommunicationProtocol


class OPCUAClient(ICommunicationProtocol):
    """Cliente OPC UA implementando a interface de comunicação"""

    def __init__(self, timeout: int = 2):
        self.timeout = timeout
        self._clients_cache: Dict[str, Client] = {}

    def _get_client(self, machine: Machine) -> Optional[Client]:
        """
        Retorna um client OPC UA para a máquina (com cache)
        """
        endpoint = machine.comunicacao.endpoint

        if endpoint in self._clients_cache:
            return self._clients_cache[endpoint]

        try:
            client = Client(endpoint, timeout=self.timeout)
            client.connect()
            self._clients_cache[endpoint] = client
            return client
        except Exception as e:
            print(f"Erro ao conectar OPC {endpoint}: {e}")
            return None

    def read_value(self, machine: Machine, tag: str) -> Optional[Any]:
        """
        Lê um valor de uma tag OPC
        """
        client = self._get_client(machine)
        if not client:
            return None

        try:
            node = client.get_node(tag)
            value = node.get_value()
            return value
        except Exception as e:
            print(f"Erro ao ler tag {tag} em {machine.nome}: {e}")
            return None

    def write_value(self, machine: Machine, tag: str, value: Any) -> bool:
        """
        Escreve um valor em uma tag OPC
        """
        client = self._get_client(machine)
        if not client:
            return False

        try:
            node = client.get_node(tag)

            # Determina o tipo de dado
            data_type = node.get_data_type_as_variant_type()

            # Cria variant com o tipo correto
            if isinstance(value, bool):
                variant = ua.Variant(value, ua.VariantType.Boolean)
            elif isinstance(value, int):
                variant = ua.Variant(value, ua.VariantType.Int32)
            elif isinstance(value, float):
                variant = ua.Variant(value, ua.VariantType.Float)
            else:
                variant = ua.Variant(value, data_type)

            node.set_value(variant)
            return True
        except Exception as e:
            print(f"Erro ao escrever tag {tag} em {machine.nome}: {e}")
            return False

    def check_connection(self, machine: Machine) -> bool:
        """
        Verifica se há conexão com a máquina (ping + OPC)
        """
        # Primeiro faz ping na rede
        if not self._check_network(machine.ip):
            return False

        # Depois tenta conectar OPC
        client = self._get_client(machine)
        return client is not None

    def _check_network(self, ip: str, port: int = 80) -> bool:
        """
        Verifica conectividade de rede usando socket
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((ip, port))
            sock.close()
            return result == 0
        except:
            return False

    def disconnect_all(self):
        """Desconecta todos os clients OPC em cache"""
        for client in self._clients_cache.values():
            try:
                client.disconnect()
            except:
                pass
        self._clients_cache.clear()

    def __del__(self):
        """Cleanup ao destruir o objeto"""
        self.disconnect_all()
