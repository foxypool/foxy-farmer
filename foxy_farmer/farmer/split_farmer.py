from abc import ABC
from typing import List

from foxy_farmer.farmer.embedded_chia_environment import EmbeddedChiaEnvironment
from foxy_farmer.farmer.farmer import Farmer


class SplitFarmer(Farmer, ABC):
    @property
    def _services_to_run_on_env(self) -> List[str]:
        return ["harvester"] if self._farmer_config.get("enable_harvester") is True else []

    @property
    def _services_to_run_on_embedded_env(self) -> List[str]:
        return ["farmer-only"]

    _embedded_environment: EmbeddedChiaEnvironment

    async def run(self) -> None:
        daemon_environment = self._environment
        if len(self._services_to_run_on_env) == 0:
            daemon_environment = self._embedded_environment

        await daemon_environment.init()
        try:
            await daemon_environment.start_daemon()
            await self._embedded_environment.start_services(self._services_to_run_on_embedded_env)
            await daemon_environment.start_services(self._services_to_run_on_env)
            await self._stop_event.wait()
        finally:
            await daemon_environment.stop_services(self._services_to_run_on_env)
            await self._embedded_environment.stop_services(self._services_to_run_on_embedded_env)
            await daemon_environment.stop_daemon()
            self._stop_event.clear()
