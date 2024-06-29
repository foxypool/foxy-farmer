from abc import ABC
from asyncio import gather
from pathlib import Path
from typing import List, Awaitable

from foxy_farmer.environment.binary_environment import BinaryEnvironment
from foxy_farmer.environment.embedded_chia_environment import EmbeddedChiaEnvironment
from foxy_farmer.farmer.farmer import Farmer
from foxy_farmer.monitoring.monitor_farmer import monitor_farmer


class HarvesterBinaryFarmer(Farmer, ABC):
    @property
    def _services_to_run_on_embedded_env(self) -> List[str]:
        return ["farmer-only"]

    _embedded_environment: EmbeddedChiaEnvironment
    _binary_environment: BinaryEnvironment
    _root_path: Path

    async def run(self) -> None:
        run_harvester = self._farmer_config.get("enable_harvester") is True
        if run_harvester:
            await self._binary_environment.init()
        try:
            await self._embedded_environment.start_daemon()
            await self._embedded_environment.start_services(self._services_to_run_on_embedded_env)
            if run_harvester:
                await self._binary_environment.start()
            futures: List[Awaitable] = [self._stop_event.wait()]
            if self._farmer_config.get("monitor_farmer_connections") is True:
                futures.append(monitor_farmer(root_path=self._root_path, until=self._stop_event))
            await gather(*futures)
        finally:
            if run_harvester:
                await self._binary_environment.stop()
            await self._embedded_environment.stop_services(self._services_to_run_on_embedded_env)
            await self._embedded_environment.stop_daemon()
            self._stop_event.clear()

    async def kill(self) -> None:
        await self._binary_environment.kill()
        await super().kill()
