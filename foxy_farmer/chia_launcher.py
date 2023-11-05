import asyncio
from asyncio import Task, create_task, Event
from logging import getLogger, Logger
from pathlib import Path
from typing import Dict, Any, Optional

from chia.daemon.client import connect_to_daemon_and_validate, DaemonProxy

from foxy_farmer.exceptions.already_running_exception import AlreadyRunningException
from foxy_farmer.foundation.daemon.daemon_proxy import get_daemon_proxy, ensure_daemon_keyring_is_unlocked
from foxy_farmer.service_factory import ServiceFactory
from foxy_farmer.util.awaitable import await_done


class ChiaLauncher:
    _foxy_root: Path
    _config: Dict[str, Any]
    _daemon_run_task: Optional[Task[None]] = None
    _logger: Logger = getLogger("chia_launcher")
    _is_shutting_down: Event = Event()
    _is_shut_down: bool = False

    def __init__(self, foxy_root: Path, config: Dict[str, Any]):
        self._foxy_root = foxy_root
        self._config = config

    async def await_shutdown(self):
        if self._daemon_run_task is None:
            return
        await await_done(self._daemon_run_task)
        self._daemon_run_task = None

    def shutdown(self):
        if self._daemon_run_task is None:
            return
        if self._is_shutting_down.is_set():
            return
        self._is_shutting_down.set()

    async def ensure_daemon_running_and_unlocked(self, quiet: bool = False, require_own_daemon: bool = True) -> None:
        daemon_proxy = await connect_to_daemon_and_validate(self._foxy_root, self._config, quiet=True)
        if daemon_proxy is not None:
            if require_own_daemon:
                self._logger.error("Another instance of foxy-farmer is already running, exiting now ..")
                await daemon_proxy.close()

                raise AlreadyRunningException

            await self._ensure_daemon_is_unlocked(daemon_proxy)
            await daemon_proxy.close()

            return

        if not quiet:
            print("Starting daemon")
        self._is_shut_down = False
        self._daemon_run_task = create_task(self._run_daemon_and_await_shutdown())
        await asyncio.sleep(1)
        try:
            await self._ensure_daemon_is_unlocked()
        except KeyboardInterrupt:
            self._is_shutting_down.set()
            await self.await_shutdown()

            raise

    async def _run_daemon_and_await_shutdown(self):
        service_factory = ServiceFactory(self._foxy_root, self._config)
        daemon_ws_server = service_factory.make_daemon()
        try:
            async with daemon_ws_server.run():
                await self._is_shutting_down.wait()
        finally:
            self._is_shutting_down.clear()
            self._is_shut_down = True

    async def _ensure_daemon_is_unlocked(self, daemon_proxy: Optional[DaemonProxy] = None):
        close_daemon_proxy = daemon_proxy is None
        if daemon_proxy is None:
            daemon_proxy = await get_daemon_proxy(self._foxy_root, self._config)
        try:
            await ensure_daemon_keyring_is_unlocked(daemon_proxy)
        finally:
            if close_daemon_proxy:
                await daemon_proxy.close()
