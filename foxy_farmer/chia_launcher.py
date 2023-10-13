import asyncio
from concurrent.futures import ThreadPoolExecutor
from logging import getLogger, Logger
from pathlib import Path
from typing import Callable, Dict, Any, Optional, Awaitable

from chia.cmds.passphrase_funcs import get_current_passphrase
from chia.daemon.client import connect_to_daemon_and_validate
from chia.daemon.server import WebSocketServer
from chia.util.keychain import Keychain

from foxy_farmer.service_factory import ServiceFactory


class ChiaLauncher:
    _foxy_root: Path
    _config: Dict[str, Any]
    _daemon_ws_server: Optional[WebSocketServer]
    _logger: Logger = getLogger("chia_launcher")

    @property
    def daemon_ws_server(self) -> Optional[WebSocketServer]:
        return self._daemon_ws_server

    def __init__(self, foxy_root: Path, config: Dict[str, Any]):
        self._foxy_root = foxy_root
        self._config = config
        service_factory = ServiceFactory(foxy_root, config)
        self._daemon_ws_server = service_factory.make_daemon()

    async def run_with_daemon(self, closure: Callable[[], Awaitable[None]]) -> None:
        if self._daemon_ws_server is None:
            self._logger.error("Another instance of foxy-farmer is already running, exiting now ..")
            exit(1)

        async with self._daemon_ws_server.run():
            await asyncio.sleep(1)
            connection = await connect_to_daemon_and_validate(self._foxy_root, self._config, quiet=True)
            while connection is None:
                self._logger.warning("Trying to connect to the daemon failed, retrying in 1 second")
                await asyncio.sleep(1)
                connection = await connect_to_daemon_and_validate(self._foxy_root, self._config, quiet=True)

            if connection is not None and await connection.is_keyring_locked():
                passphrase = Keychain.get_cached_master_passphrase()
                if passphrase is None or not Keychain.master_passphrase_is_valid(passphrase):
                    with ThreadPoolExecutor(max_workers=1, thread_name_prefix="get_current_passphrase") as executor:
                        passphrase = await asyncio.get_running_loop().run_in_executor(executor, get_current_passphrase)

                if passphrase:
                    print("Unlocking daemon keyring")
                    await connection.unlock_keyring(passphrase)

            await closure()

    async def wait_for_ready(self):
        is_ready = await self.is_ready()
        while is_ready is False:
            await asyncio.sleep(1)
            is_ready = await self.is_ready()

    async def is_ready(self):
        connection = await connect_to_daemon_and_validate(self._foxy_root, self._config, quiet=True)

        return connection is not None and await connection.is_keyring_locked() is False
