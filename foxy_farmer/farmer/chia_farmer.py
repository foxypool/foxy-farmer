from abc import ABC
from asyncio import gather
from pathlib import Path
from typing import List, Awaitable

from foxy_farmer.environment.chia_environment import ChiaEnvironment
from foxy_farmer.farmer.farmer import Farmer
from foxy_farmer.monitoring.monitor_farmer import monitor_farmer


class ChiaFarmer(Farmer, ABC):
    @property
    def _services_to_run(self) -> List[str]:
        services = ["farmer-only"]
        if self._farmer_config.get("enable_harvester") is True:
            services.append("harvester")

        return services

    _environment: ChiaEnvironment
    _root_path: Path

    async def run(self) -> None:
        await self._environment.init()
        try:
            await self._environment.start_daemon()
            await self._environment.start_services(self._services_to_run)
            futures: List[Awaitable] = [self._stop_event.wait()]
            if self._farmer_config.get("monitor_farmer_connections") is True:
                futures.append(monitor_farmer(root_path=self._root_path, until=self._stop_event))
            await gather(*futures)
        finally:
            await self._environment.stop_services(self._services_to_run)
            await self._environment.stop_daemon()
            self._stop_event.clear()

    async def kill(self) -> None:
        await self._environment.kill()
        await super().kill()
