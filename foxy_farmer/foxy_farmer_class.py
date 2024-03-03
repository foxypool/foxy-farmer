from asyncio import new_event_loop
from logging import Logger, getLogger
from pathlib import Path
from signal import SIGINT
from sys import platform
from typing import Optional

from sentry_sdk.sessions import auto_session_tracking

from foxy_farmer.farmer.bladebit_farmer import BladebitFarmer
from foxy_farmer.farmer.dr_plotter_farmer import DrPlotterFarmer
from foxy_farmer.farmer.farmer import Farmer
from foxy_farmer.farmer.gigahorse_farmer import GigahorseFarmer
from foxy_farmer.config.backend import Backend
from foxy_farmer.config.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_farmer.config.foxy_config_manager import FoxyConfigManager
from foxy_farmer.ff_logging.configure_logging import initialize_logging_with_stdout
from foxy_farmer.util.node_id import calculate_harvester_node_id_slug


class FoxyFarmer:
    _foxy_root: Path
    _config_path: Path
    _farmer: Optional[Farmer] = None
    _logger: Logger = getLogger("foxy_farmer")

    def __init__(self, foxy_root: Path, config_path: Path):
        self._foxy_root = foxy_root
        self._config_path = config_path

    async def run(self):
        foxy_chia_config_manager = FoxyChiaConfigManager(self._foxy_root)
        await foxy_chia_config_manager.ensure_foxy_config(self._config_path)

        from chia.util.config import load_config
        config = load_config(self._foxy_root, "config.yaml")

        initialize_logging_with_stdout(
            logging_config=config["logging"],
            root_path=self._foxy_root,
        )

        foxy_config_manager = FoxyConfigManager(self._config_path)
        foxy_config = foxy_config_manager.load_config()

        backend = foxy_config.get("backend", Backend.BladeBit)
        if backend == Backend.BladeBit:
            self._farmer = BladebitFarmer(root_path=self._foxy_root, farmer_config=foxy_config)
        elif backend == Backend.Gigahorse:
            self._farmer = GigahorseFarmer(root_path=self._foxy_root, farmer_config=foxy_config)
        elif backend == Backend.DrPlotter:
            self._farmer = DrPlotterFarmer(root_path=self._foxy_root, farmer_config=foxy_config)
        else:
            self._logger.error(f"Backend '{backend}' is not supported!")

            return

        if not self._farmer.supports_system:
            self._logger.error(f"Backend '{backend}' does not support your system!")

            return

        from foxy_farmer.version import version
        status_infos = f"Foxy-Farmer version={version} backend={backend}"
        if foxy_config.get("enable_harvester") is True:
            status_infos += f" harvester_id={calculate_harvester_node_id_slug(self._foxy_root, config)}"
        status_infos += f" config_path={self._config_path}"
        self._logger.info(status_infos)

        with auto_session_tracking(session_mode="application"):
            await self._farmer.run()

    async def stop(self) -> None:
        if self._farmer is not None:
            await self._farmer.stop()

    async def kill(self) -> None:
        if self._farmer is not None:
            await self._farmer.kill()

    def setup_window_close_handler(self) -> None:
        if platform == "win32" or platform == "cygwin":
            from win32api import SetConsoleCtrlHandler

            def on_exit(sig, func=None):
                # Only handle window closes (x)
                if sig != SIGINT:
                    return
                new_loop = new_event_loop()
                new_loop.run_until_complete(new_loop.create_task(self.kill()))

            SetConsoleCtrlHandler(on_exit, True)
