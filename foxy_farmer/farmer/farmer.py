from abc import ABC
from asyncio import Event, sleep
from typing import List, Any, Dict

from foxy_farmer.farmer.chia_environment import ChiaEnvironment


class Farmer(ABC):
    @property
    def _services_to_run(self) -> List[str]:
        services = ["farmer-only"]
        if self._farmer_config.get("enable_harvester") is True:
            services.append("harvester")

        return services

    _environment: ChiaEnvironment
    _farmer_config: Dict[str, Any]
    _stop_event: Event = Event()

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

    async def stop(self) -> None:
        self._stop_event.set()
        while self._stop_event.is_set():
            await sleep(0.1)
