from pathlib import Path
from typing import Dict, Optional

from chia.consensus.default_constants import DEFAULT_CONSTANTS
from chia.daemon.server import daemon_launch_lock_path, log, WebSocketServer
from chia.server.outbound_message import NodeType
from chia.server.start_farmer import create_farmer_service
from chia.server.start_harvester import create_harvester_service
from chia.server.start_wallet import create_wallet_service
from chia.types.aliases import FarmerService, WalletService, HarvesterService
from chia.util.chia_version import chia_short_version
from chia.util.config import get_unresolved_peer_infos
from chia.util.lock import Lockfile, LockfileError


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
                log.info(f"chia-blockchain version: {chia_short_version()}")

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

    def make_harvester(self) -> HarvesterService:
        service_config = self._config["harvester"]
        farmer_peers = get_unresolved_peer_infos(service_config, NodeType.FARMER)

        return create_harvester_service(self._root_path, self._config, DEFAULT_CONSTANTS, farmer_peers)

    def make_farmer(self) -> FarmerService:
        return create_farmer_service(self._root_path, self._config, self._config["pool"], DEFAULT_CONSTANTS)

    def make_wallet(self) -> WalletService:
        return create_wallet_service(self._root_path, self._config, DEFAULT_CONSTANTS)
