import asyncio
import sys
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
    _did_launch_daemon = False
    _is_shut_down = False

    @property
    def is_shut_down(self) -> bool:
        return self._is_shut_down

    @property
    def daemon_ws_server(self) -> Optional[WebSocketServer]:
        return self._daemon_ws_server

    def __init__(self, foxy_root: Path, config: Dict[str, Any]):
        self._foxy_root = foxy_root
        self._config = config
        service_factory = ServiceFactory(foxy_root, config)
        self._daemon_ws_server = service_factory.make_daemon()

    async def run_with_daemon(self, closure: Callable[[], Awaitable[None]], quiet: bool = False) -> None:
        if self._daemon_ws_server is None:
            print("Another instance of foxy-farmer is already running, exiting now ..", file=sys.stderr)
            await self.daemon_ws_server.stop()
            self._is_shut_down = True

            return

        connection = await connect_to_daemon_and_validate(self._foxy_root, self._config, quiet=True)
        if connection is not None:
            print("Another instance of foxy-farmer is already running, exiting now ..", file=sys.stderr)
            await self.daemon_ws_server.stop()
            self._is_shut_down = True

            return

        if not quiet:
            print("Starting daemon")
        async with self._daemon_ws_server.run():
            self._did_launch_daemon = True
            await asyncio.sleep(1)
            try:
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
            finally:
                self._is_shut_down = True

    async def wait_for_ready_or_shutdown(self):
        if self._is_shut_down:
            return
        is_ready = await self.is_ready()
        while is_ready is False:
            await asyncio.sleep(1)
            if self._is_shut_down:
                return
            is_ready = await self.is_ready()

    async def is_ready(self):
        if self._did_launch_daemon is False:
            return False

        connection = await connect_to_daemon_and_validate(self._foxy_root, self._config, quiet=True)

        return connection is not None and await connection.is_keyring_locked() is False
