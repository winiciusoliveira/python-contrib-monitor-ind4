from typing import Optional, Any
import socket
import subprocess
import platform
from ...domain.models import Machine
from ...domain.interfaces import ICommunicationProtocol


class NetworkClient(ICommunicationProtocol):
    """Cliente para verificação de conectividade de rede"""

    def __init__(self, timeout: int = 1):
        self.timeout = timeout

    def read_value(self, machine: Machine, tag: str) -> Optional[Any]:
        """
        Não aplicável para rede simples
        """
        return None

    def write_value(self, machine: Machine, tag: str, value: Any) -> bool:
        """
        Não aplicável para rede simples
        """
        return False

    def check_connection(self, machine: Machine) -> bool:
        """
        Verifica conectividade via ping
        """
        return self.ping(machine.ip)

    def ping(self, host: str) -> bool:
        """
        Executa ping no host
        """
        # Método 1: Usando socket (mais rápido)
        if self._check_socket(host):
            return True

        # Método 2: Ping via subprocess (fallback)
        return self._check_ping(host)

    def _check_socket(self, host: str, port: int = 80) -> bool:
        """
        Verifica conectividade usando socket
        """
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(self.timeout)
            result = sock.connect_ex((host, port))
            sock.close()
            return result == 0
        except:
            return False

    def _check_ping(self, host: str) -> bool:
        """
        Executa comando ping do sistema
        """
        try:
            param = '-n' if platform.system().lower() == 'windows' else '-c'
            command = ['ping', param, '1', '-w', str(self.timeout * 1000), host]

            result = subprocess.run(
                command,
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                timeout=self.timeout + 1
            )

            return result.returncode == 0
        except:
            return False
