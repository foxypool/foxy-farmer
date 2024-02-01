from asyncio import AbstractEventLoop
from logging import Logger, getLogger
from pathlib import Path
from signal import Signals
from types import FrameType
from typing import Optional

from chia.util.misc import SignalHandlers
from sentry_sdk.sessions import auto_session_tracking

from foxy_farmer.farmer.bladebit_farmer import BladebitFarmer
from foxy_farmer.farmer.farmer import Farmer
from foxy_farmer.farmer.gigahorse_farmer import GigahorseFarmer
from foxy_farmer.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_farmer.foxy_config_manager import FoxyConfigManager
from foxy_farmer.logging.configure_logging import initialize_logging_with_stdout
from foxy_farmer.util.node_id import calculate_harvester_node_id_slug


class FoxyFarmer:
    _foxy_root: Path
    _config_path: Path
    _farmer: Optional[Farmer]
    _logger: Logger = getLogger("foxy_farmer")

    def __init__(self, foxy_root: Path, config_path: Path):
        self._foxy_root = foxy_root
        self._config_path = config_path

    async def run(self):
        foxy_chia_config_manager = FoxyChiaConfigManager(self._foxy_root)
        foxy_chia_config_manager.ensure_foxy_config(self._config_path)

        from chia.util.config import load_config
        config = load_config(self._foxy_root, "config.yaml")

        initialize_logging_with_stdout(
            logging_config=config["logging"],
            root_path=self._foxy_root,
        )

        foxy_config_manager = FoxyConfigManager(self._config_path)
        foxy_config = foxy_config_manager.load_config()

        from foxy_farmer.version import version
        backend = foxy_config.get("backend", "bladebit")
        status_infos = f"Foxy-Farmer version={version} backend={backend}"
        if foxy_config.get("enable_harvester") is True:
            status_infos += f" harvester_id={calculate_harvester_node_id_slug(self._foxy_root, config)}"
        status_infos += f" config_path={self._config_path}"
        self._logger.info(status_infos)

        if backend == "bladebit":
            self._farmer = BladebitFarmer(root_path=self._foxy_root, farmer_config=foxy_config)
        elif backend == "gigahorse":
            self._farmer = GigahorseFarmer(root_path=self._foxy_root, farmer_config=foxy_config)
        else:
            raise ValueError(f"Backend '{backend}' is not supported!")

        with auto_session_tracking(session_mode="application"):
            await self._farmer.run()

    async def _accept_signal(
            self,
            signal_: Signals,
            stack_frame: Optional[FrameType],
            loop: AbstractEventLoop,
    ) -> None:
        if self._farmer is not None:
            await self._farmer.stop()

    async def setup_process_global_state(self) -> None:
        async with SignalHandlers.manage() as signal_handlers:
            signal_handlers.setup_async_signal_handler(handler=self._accept_signal)
