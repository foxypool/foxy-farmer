from chia.server.outbound_message import NodeType
from chia.server.start_service import Service
from chia.types.peer_info import PeerInfo
from chia.util.ints import uint16
from chia.util.network import get_host_addr


class ServiceWrapper:
    service: Service

    def __init__(self, service: Service):
        self.service = service

    @property
    def reconnect_tasks(self):
        return self.service._reconnect_tasks

    def has_active_connections(self, node_type: NodeType):
        return len(self.service._server.get_connections(node_type=node_type)) > 0

    def remove_all_peers(self):
        for task in self.reconnect_tasks.values():
            if task is not None:
                task.cancel()
        self.reconnect_tasks.clear()

    def add_peer_with_hostname(self, hostname: str, port: uint16):
        self.service.add_peer(
            PeerInfo(str(get_host_addr(hostname, prefer_ipv6=self.service.config.get("prefer_ipv6", False))), port)
        )
