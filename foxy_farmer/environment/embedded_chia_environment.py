from asyncio import create_task, Task, Event, sleep
from logging import Logger, getLogger
from pathlib import Path
from typing import Any, Dict, Optional, List

from chia.daemon.client import connect_to_daemon_and_validate, DaemonProxy
from chia.farmer.farmer import Farmer
from chia.farmer.farmer_api import FarmerAPI
from chia.harvester.harvester import Harvester
from chia.harvester.harvester_api import HarvesterAPI
from chia.server.start_service import Service
from chia.util.service_groups import services_for_groups
from chia.wallet.wallet_node import WalletNode
from chia.wallet.wallet_node_api import WalletNodeAPI

from foxy_farmer.exceptions.already_running_exception import AlreadyRunningException
from foxy_farmer.environment.chia_environment import ChiaEnvironment
from foxy_farmer.daemon.daemon_proxy import get_daemon_proxy, ensure_daemon_keyring_is_unlocked
from foxy_farmer.environment.service.service_factory import ServiceFactory
from foxy_farmer.util.awaitable import await_done


class EmbeddedChiaEnvironment(ChiaEnvironment):
    _logger: Logger = getLogger("embedded_chia_environment")
    _service_factory: ServiceFactory
    _daemon_run_task: Optional[Task[None]] = None
    _daemon_proxy: Optional[DaemonProxy] = None
    _shut_down_daemon_event: Event = Event()
    _farmer_service: Optional[Service[Farmer, FarmerAPI]] = None
    _farmer_run_task: Optional[Task[None]] = None
    _harvester_service: Optional[Service[Harvester, HarvesterAPI]] = None
    _harvester_run_task: Optional[Task[None]] = None
    _wallet_service: Optional[Service[WalletNode, WalletNodeAPI]] = None
    _wallet_run_task: Optional[Task[None]] = None

    def __init__(self, root_path: Path, config: Dict[str, Any], allow_connecting_to_existing_daemon: bool):
        self.root_path = root_path
        self.config = config
        self.allow_connecting_to_existing_daemon = allow_connecting_to_existing_daemon
        self._service_factory = ServiceFactory(root_path=root_path, config=config)

    async def start_daemon(self) -> None:
        if self._daemon_proxy is not None:
            return
        self._daemon_proxy = await connect_to_daemon_and_validate(self.root_path, self.config, quiet=True)
        if self._daemon_proxy is not None:
            if not self.allow_connecting_to_existing_daemon:
                self._logger.error("Another instance of foxy-farmer is already running, exiting now ..")

                raise AlreadyRunningException

            await ensure_daemon_keyring_is_unlocked(self._daemon_proxy)

            return

        self._daemon_run_task = create_task(self._run_daemon_and_await_shutdown())
        await sleep(1)
        self._daemon_proxy = await get_daemon_proxy(self.root_path, self.config)
        await ensure_daemon_keyring_is_unlocked(self._daemon_proxy)

    async def stop_daemon(self) -> None:
        if self._daemon_proxy is not None:
            await self._daemon_proxy.close()
            self._daemon_proxy = None

        if self._daemon_run_task is not None:
            self._shut_down_daemon_event.set()
            await await_done(self._daemon_run_task)
            self._daemon_run_task = None

    async def start_services(self, service_names: List[str]) -> None:
        for service in services_for_groups(service_names):
            if service == "chia_farmer" and self._farmer_service is None:
                self._farmer_service = self._service_factory.make_farmer()
                self._farmer_run_task = create_task(self._farmer_service.run())
            elif service == "chia_harvester" and self._harvester_service is None:
                self._harvester_service = self._service_factory.make_harvester()
                self._harvester_run_task = create_task(self._harvester_service.run())
            elif service == "chia_wallet" and self._wallet_service is None:
                self._wallet_service = self._service_factory.make_wallet()
                self._wallet_run_task = create_task(self._wallet_service.run())

    async def stop_services(self, service_names: List[str]) -> None:
        for service in services_for_groups(service_names):
            if service == "chia_farmer" and self._farmer_service is not None:
                self._farmer_service.stop_requested.set()
                self._farmer_service = None
                await await_done(self._farmer_run_task)
                self._farmer_run_task = None
            elif service == "chia_harvester" and self._harvester_service is not None:
                self._harvester_service.stop_requested.set()
                self._harvester_service = None
                await await_done(self._harvester_run_task)
                self._harvester_run_task = None
            elif service == "chia_wallet" and self._wallet_service is not None:
                self._wallet_service.stop_requested.set()
                self._wallet_service = None
                await await_done(self._wallet_run_task)
                self._wallet_run_task = None

    async def _run_daemon_and_await_shutdown(self):
        daemon_ws_server = self._service_factory.make_daemon()
        try:
            async with daemon_ws_server.run():
                await self._shut_down_daemon_event.wait()
        finally:
            self._shut_down_daemon_event.clear()
            self._daemon_run_task = None
