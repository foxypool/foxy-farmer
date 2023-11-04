from asyncio import AbstractEventLoop
from logging import Logger, getLogger
from pathlib import Path
from signal import Signals
from types import FrameType
from typing import Optional

from chia.farmer.farmer import Farmer
from chia.farmer.farmer_api import FarmerAPI
from chia.harvester.harvester import Harvester
from chia.harvester.harvester_api import HarvesterAPI
from chia.server.start_service import Service
from chia.util.misc import SignalHandlers
from sentry_sdk.sessions import auto_session_tracking

from foxy_farmer.chia_launcher import ChiaLauncher
from foxy_farmer.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_farmer.foxy_config_manager import FoxyConfigManager
from foxy_farmer.service_factory import ServiceFactory


class FoxyFarmer:
    _foxy_root: Path
    _config_path: Path
    _chia_launcher: Optional[ChiaLauncher]
    _farmer_service: Optional[Service[Farmer, FarmerAPI]] = None
    _harvester_service: Optional[Service[Harvester, HarvesterAPI]] = None
    _logger: Logger = getLogger("foxy_farmer")

    def __init__(self, foxy_root: Path, config_path: Path):
        self._foxy_root = foxy_root
        self._config_path = config_path

    async def start(self):
        foxy_chia_config_manager = FoxyChiaConfigManager(self._foxy_root)
        foxy_chia_config_manager.ensure_foxy_config(self._config_path)

        from chia.util.config import load_config
        config = load_config(self._foxy_root, "config.yaml")

        from foxy_farmer.foxy_farmer_logging import initialize_logging_with_stdout
        initialize_logging_with_stdout(
            logging_config=config["logging"],
            root_path=self._foxy_root,
        )

        from foxy_farmer.version import version
        self._logger.info(f"Foxy-Farmer {version} using config in {self._config_path}")

        self._chia_launcher = ChiaLauncher(foxy_root=self._foxy_root, config=config)
        await self._chia_launcher.ensure_daemon_running_and_unlocked(quiet=True)

        service_factory = ServiceFactory(self._foxy_root, config)
        self._farmer_service = service_factory.make_farmer()

        foxy_config_manager = FoxyConfigManager(self._config_path)
        foxy_config = foxy_config_manager.load_config()
        if foxy_config.get("enable_harvester") is True:
            self._harvester_service = service_factory.make_harvester()

        await self.start_and_await_services()

    async def start_and_await_services(self):
        # Do not log farmer id as it is not tracked yet
        # log.info(f"Farmer starting (id={self._farmer_service._node.server.node_id.hex()[:8]})")

        awaitables = [
            self._chia_launcher.await_shutdown(),
            self._farmer_service.run(),
        ]

        if self._harvester_service is not None:
            self._logger.info(f"Harvester starting (id={self._harvester_service._node.server.node_id.hex()[:8]})")
            awaitables.append(self._harvester_service.run())

        with auto_session_tracking(session_mode="application"):
            from asyncio import gather
            await gather(*awaitables)

    def stop(self):
        if self._harvester_service is not None:
            self._harvester_service.stop()
        if self._farmer_service is not None:
            self._farmer_service.stop()
        if self._chia_launcher is not None:
            self._chia_launcher.shutdown()

    def _accept_signal(
            self,
            signal_: Signals,
            stack_frame: Optional[FrameType],
            loop: AbstractEventLoop,
    ) -> None:
        self.stop()

    async def setup_process_global_state(self) -> None:
        async with SignalHandlers.manage() as signal_handlers:
            signal_handlers.setup_sync_signal_handler(handler=self._accept_signal)
