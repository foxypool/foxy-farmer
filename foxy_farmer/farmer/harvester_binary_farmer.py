from abc import ABC
from typing import List

from foxy_farmer.environment.binary_environment import BinaryEnvironment
from foxy_farmer.environment.embedded_chia_environment import EmbeddedChiaEnvironment
from foxy_farmer.farmer.farmer import Farmer


class HarvesterBinaryFarmer(Farmer, ABC):
    @property
    def _services_to_run_on_embedded_env(self) -> List[str]:
        return ["farmer-only"]

    _embedded_environment: EmbeddedChiaEnvironment
    _binary_environment: BinaryEnvironment

    async def run(self) -> None:
        run_harvester = self._farmer_config.get("enable_harvester") is True
        if run_harvester:
            await self._binary_environment.init()
        try:
            await self._embedded_environment.start_daemon()
            await self._embedded_environment.start_services(self._services_to_run_on_embedded_env)
            if run_harvester:
                await self._binary_environment.start()
            await self._stop_event.wait()
        finally:
            if run_harvester:
                await self._binary_environment.stop()
            await self._embedded_environment.stop_services(self._services_to_run_on_embedded_env)
            await self._embedded_environment.stop_daemon()
            self._stop_event.clear()
