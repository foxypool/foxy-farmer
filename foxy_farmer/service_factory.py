from pathlib import Path
from typing import Dict, Optional

from chia.cmds.init_funcs import chia_full_version_str
from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.daemon.server import daemon_launch_lock_path, log, WebSocketServer
from chia.server.start_farmer import create_farmer_service
from chia.server.start_harvester import create_harvester_service
from chia.types.peer_info import UnresolvedPeerInfo
from chia.util.ints import uint16
from chia.util.lock import Lockfile, LockfileError

from foxy_farmer.foxy_farming_gateway import eu1_foxy_farming_gateway_address, foxy_farming_gateway_port, \
    eu3_foxy_farming_gateway_address


class ServiceFactory:
    _root_path: Path
    _config: Dict

    def __init__(self, root_path: Path, config: Dict):
        self._root_path = root_path
        self._config = config

    def make_daemon(self) -> Optional[WebSocketServer]:
        crt_path = self._root_path / self._config["daemon_ssl"]["private_crt"]
        key_path = self._root_path / self._config["daemon_ssl"]["private_key"]
        ca_crt_path = self._root_path / self._config["private_ssl_ca"]["crt"]
        ca_key_path = self._root_path / self._config["private_ssl_ca"]["key"]
        try:
            with Lockfile.create(daemon_launch_lock_path(self._root_path), timeout=1):
                log.info(f"chia-blockchain version: {chia_full_version_str()}")

                ws_server = WebSocketServer(
                    self._root_path,
                    ca_crt_path,
                    ca_key_path,
                    crt_path,
                    key_path,
                )

                return ws_server
        except LockfileError:
            print("daemon: already launching")
            return None

    def make_harvester(self):
        farmer_peer = UnresolvedPeerInfo(
            str(self._config["harvester"]["farmer_peer"]["host"]),
            self._config["harvester"]["farmer_peer"]["port"]
        )

        return create_harvester_service(self._root_path, self._config, DEFAULT_CONSTANTS, farmer_peer)

    def make_farmer(self):
        service = create_farmer_service(self._root_path, self._config, self._config["pool"], DEFAULT_CONSTANTS)
        service.add_peer(UnresolvedPeerInfo(host=eu1_foxy_farming_gateway_address, port=uint16(foxy_farming_gateway_port)))
        service.add_peer(UnresolvedPeerInfo(host=eu3_foxy_farming_gateway_address, port=uint16(foxy_farming_gateway_port)))

        return service
