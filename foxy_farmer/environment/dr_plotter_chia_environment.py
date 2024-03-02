import os
from logging import getLogger
from pathlib import Path
from subprocess import Popen
from typing import Any, Dict

from foxy_farmer.binary_manager.dr_plotter_binary_manager import DrPlotterBinaryManager
from foxy_farmer.config.foxy_config import FoxyConfig
from foxy_farmer.environment.binary_chia_environment import BinaryChiaEnvironment


class DrPlotterChiaEnvironment(BinaryChiaEnvironment):
    def __init__(
            self,
            root_path: Path,
            config: Dict[str, Any],
            allow_connecting_to_existing_daemon: bool,
            farmer_config: FoxyConfig,
    ):
        self._logger = getLogger("dr_plotter_chia_environment")
        self._binary_manager = DrPlotterBinaryManager()
        super().__init__(root_path, config, allow_connecting_to_existing_daemon, farmer_config)

    def _start_daemon_process(self) -> Popen:
        os.environ["CHIA_ROOT"] = str(self.root_path)
        if self._farmer_config.get("dr_plotter_client_token") is not None:
            os.environ["DRPLOTTER_CLIENT_TOKEN"] = str(self._farmer_config["dr_plotter_client_token"])

        return super()._start_daemon_process()

