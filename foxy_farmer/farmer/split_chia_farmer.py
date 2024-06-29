from abc import ABC
from asyncio import gather
from pathlib import Path
from typing import List, Awaitable

from foxy_farmer.environment.chia_environment import ChiaEnvironment
from foxy_farmer.environment.embedded_chia_environment import EmbeddedChiaEnvironment
from foxy_farmer.farmer.farmer import Farmer
from foxy_farmer.monitoring.monitor_farmer import monitor_farmer


class SplitChiaFarmer(Farmer, ABC):
    @property
    def _services_to_run_on_env(self) -> List[str]:
        return ["harvester"] if self._farmer_config.get("enable_harvester") is True else []

    @property
    def _services_to_run_on_embedded_env(self) -> List[str]:
        return ["farmer-only"]

    @property
    def _daemon_environment(self) -> ChiaEnvironment:
        return self._embedded_environment if len(self._services_to_run_on_env) == 0 else self._environment

    _environment: ChiaEnvironment
    _embedded_environment: EmbeddedChiaEnvironment
    _root_path: Path

    async def run(self) -> None:
        daemon_environment = self._daemon_environment

        await daemon_environment.init()
        try:
            await daemon_environment.start_daemon()
            await self._embedded_environment.start_services(self._services_to_run_on_embedded_env)
            await daemon_environment.start_services(self._services_to_run_on_env)
            futures: List[Awaitable] = [self._stop_event.wait()]
            if self._farmer_config.get("monitor_farmer_connections") is True:
                futures.append(monitor_farmer(root_path=self._root_path, until=self._stop_event))
            await gather(*futures)
        finally:
            await daemon_environment.stop_services(self._services_to_run_on_env)
            await self._embedded_environment.stop_services(self._services_to_run_on_embedded_env)
            await daemon_environment.stop_daemon()
            self._stop_event.clear()

    async def kill(self) -> None:
        await self._daemon_environment.kill()
        await super().kill()
