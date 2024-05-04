import sys
from asyncio import Task, create_task, sleep
from logging import getLogger
from os import remove
from os.path import join
from sys import platform
from pathlib import Path
from platform import libc_ver, machine, system
from shutil import move
from tempfile import TemporaryDirectory
from typing import Optional, Dict, Any, Callable

from aiohttp import ClientSession, ClientTimeout
from packaging.version import Version

from foxy_farmer.download.download_manager import DownloadManager
from foxy_farmer.util.is_binary import is_binary
from foxy_farmer.util.ssl_context import ssl_context
from foxy_farmer.version import version as current_version


class SelfUpdateManager:
    @property
    def is_supported(self) -> bool:
        return is_binary()

    @property
    def _binary_file_name_in_archive(self):
        binary_suffix = ".exe" if platform == "win32" else ""

        return f"foxy-farmer{binary_suffix}"

    @property
    def _binary_path(self) -> Path:
        if not is_binary():
            raise RuntimeError("Can not determine binary path for non binary install")

        return Path(sys.executable)

    @property
    def _old_binary_path(self) -> Path:
        binary_suffix = ".exe" if platform == "win32" else ""

        return self._binary_path.with_suffix(f".old{binary_suffix}")

    @property
    def _binary_archive_name(self) -> str:
        prefix = "foxy-farmer-"
        if platform == "win32":
            return f"{prefix}windows.zip"

        if system() == "Darwin":
            prefix = f"{prefix}macos"
            if machine() == "aarch64":
                return f"{prefix}-arm64.zip"

            return f"{prefix}.zip"

        prefix = f"{prefix}ubuntu"
        [_, libc_version] = libc_ver()
        if Version(libc_version) < Version("2.35"):
            return f"{prefix}-20.04.zip"

        return f"{prefix}.zip"

    did_update: bool = False
    _download_manager: DownloadManager = DownloadManager()
    _logger = getLogger("self_updater")
    _periodic_update_task: Optional[Task[None]] = None
    _shut_down: bool = False

    async def shutdown(self):
        self._shut_down = True
        if self._periodic_update_task is not None:
            await self._periodic_update_task

    def start_periodic_update_check(self, on_update_completed: Callable) -> None:
        async def periodic_update_check():
            time_slept = 0
            while not self.did_update and not self._shut_down:
                if time_slept >= 60 * 60:
                    try:
                        await self.update(is_silent=True)
                    except Exception as e:
                        self._logger.error(f"Encountered an error during the periodic update check: {e}")
                    time_slept = 0
                else:
                    time_slept += 1
                    await sleep(1)
            if self.did_update:
                await on_update_completed()

        self._periodic_update_task = create_task(periodic_update_check())

    async def update(self, is_silent: bool = False) -> None:
        if not self.is_supported:
            if not is_silent:
                self._logger.warning("Self-Update not supported on non-binary installs")

            return
        version_to_update_to = await self._check_for_version_update()
        if version_to_update_to is None:
            if not is_silent:
                self._logger.info("Already using the latest version")

            return

        self._logger.info(f"New version detected, starting self-update from {current_version} to {version_to_update_to} ..")
        await self._replace_with_binary(version_to_update_to)
        self.did_update = True
        self._logger.info(f"✅ Completed self-update to {version_to_update_to}, restarting ..")

    async def _replace_with_binary(self, version: str):
        file_description = f"Foxy-Farmer {version}"
        with TemporaryDirectory() as temp_dir:
            await self._download_manager.download_archive_and_extract(
                file_url=f"https://downloads.foxypool.io/chia/foxy-farmer/{version}/{self._binary_archive_name}",
                file_name=self._binary_archive_name,
                to_path=temp_dir,
                file_description=file_description,
            )
            self._swap_binary(Path(join(temp_dir, self._binary_file_name_in_archive)))

    def _swap_binary(self, new_binary_path: Path):
        if self._old_binary_path.exists():
            remove(self._old_binary_path)
        move(self._binary_path, self._old_binary_path)
        move(new_binary_path, self._binary_path)

    async def _check_for_version_update(self) -> Optional[str]:
        releases = await self._get_foxy_farmer_release_list()
        latest_version = releases["entries"]["latest"]["pointsTo"]
        if Version(current_version) >= Version(latest_version):
            return None

        return latest_version

    async def _get_foxy_farmer_release_list(self) -> Dict[str, Any]:
        async with ClientSession(timeout=ClientTimeout(total=30)) as client:
            async with client.get("https://downloads.foxypool.io/chia/foxy-farmer?format=json", ssl=ssl_context) as res:
                return await res.json()
