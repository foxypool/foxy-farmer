from abc import ABC
from typing import List

from foxy_farmer.environment.chia_environment import ChiaEnvironment
from foxy_farmer.farmer.farmer import Farmer


class ChiaFarmer(Farmer, ABC):
    @property
    def _services_to_run(self) -> List[str]:
        services = ["farmer-only"]
        if self._farmer_config.get("enable_harvester") is True:
            services.append("harvester")

        return services

    _environment: ChiaEnvironment

    async def run(self) -> None:
        await self._environment.init()
        try:
            await self._environment.start_daemon()
            await self._environment.start_services(self._services_to_run)
            await self._stop_event.wait()
        finally:
            await self._environment.stop_services(self._services_to_run)
            await self._environment.stop_daemon()
            self._stop_event.clear()

    async def kill(self) -> None:
        await self._environment.kill()
        await super().kill()
