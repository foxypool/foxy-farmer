from abc import ABC
from asyncio import Event, sleep

from foxy_farmer.config.foxy_config import FoxyConfig


class Farmer(ABC):
    @property
    def supports_system(self) -> bool:
        return True

    _farmer_config: FoxyConfig
    _stop_event: Event = Event()

    async def run(self) -> None:
        ...

    async def stop(self) -> None:
        self._stop_event.set()
        while self._stop_event.is_set():
            await sleep(0.1)

    async def kill(self) -> None:
        await self.stop()
