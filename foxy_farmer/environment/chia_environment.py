from pathlib import Path
from typing import Protocol, Dict, Any, List


class ChiaEnvironment(Protocol):
    root_path: Path
    config: Dict[str, Any]
    allow_connecting_to_existing_daemon: bool

    async def init(self) -> None:
        pass

    async def start_daemon(self) -> None:
        ...

    async def stop_daemon(self) -> None:
        ...

    async def start_services(self, service_names: List[str]) -> None:
        ...

    async def stop_services(self, service_names: List[str]) -> None:
        ...

    async def kill(self):
        await self.stop_daemon()
