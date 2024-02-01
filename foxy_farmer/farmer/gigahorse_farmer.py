from asyncio import Task, create_task
from pathlib import Path
from sys import platform
from typing import Any, Dict, Optional
from platform import system, machine

from chia.util.config import load_config

from foxy_farmer.farmer.gigahorse_chia_environment import GigahorseChiaEnvironment
from foxy_farmer.farmer.farmer import Farmer
from foxy_farmer.ff_logging.syslog_server import SyslogServer


class GigahorseFarmer(Farmer):
    @property
    def supports_system(self) -> bool:
        arch = machine()
        if platform == "win32":
            return arch == "AMD64"
        if system() == "Linux":
            return arch == "x86_64" or arch == "aarch64" or arch.lower() == "amd64"

        return False

    _syslog_server: SyslogServer
    _syslog_run_task: Optional[Task[None]] = None

    def __init__(self, root_path: Path, farmer_config: Dict[str, Any]):
        self._farmer_config = farmer_config
        config = load_config(root_path, "config.yaml")
        self._environment = GigahorseChiaEnvironment(
            root_path=root_path,
            config=config,
            allow_connecting_to_existing_daemon=False,
            farmer_config=farmer_config,
        )
        self._syslog_server = SyslogServer(logging_config=config["logging"])

    async def run(self) -> None:
        if self._syslog_run_task is None:
            self._syslog_run_task = create_task(self._syslog_server.run())
        await super().run()

    async def stop(self) -> None:
        await super().stop()
        self._syslog_server.stop()
        self._syslog_run_task = None
