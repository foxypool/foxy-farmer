import os
import subprocess
from logging import Logger, getLogger
from os.path import join
from pathlib import Path
from subprocess import Popen
from sys import platform
from typing import Any, Dict, Optional, List

from chia.daemon.client import connect_to_daemon_and_validate, DaemonProxy
from chia.util.service_groups import services_for_groups

from foxy_farmer.binary_manager.binary_manager import BinaryManager
from foxy_farmer.binary_manager.gigahorse_binary_manager import GigahorseBinaryManager
from foxy_farmer.exceptions.already_running_exception import AlreadyRunningException
from foxy_farmer.farmer.chia_environment import ChiaEnvironment
from foxy_farmer.foundation.daemon.daemon_proxy import get_daemon_proxy, ensure_daemon_keyring_is_unlocked


class GigahorseChiaEnvironment(ChiaEnvironment):
    _farmer_config: Dict[str, Any]
    _logger: Logger = getLogger("gigahorse_chia_environment")
    _binary_manager: BinaryManager = GigahorseBinaryManager()
    _binary_directory_path: Optional[Path] = None
    _chia_daemon_process: Optional[Popen] = None
    _daemon_proxy: Optional[DaemonProxy] = None

    def __init__(
        self,
        root_path: Path,
        config: Dict[str, Any],
        allow_connecting_to_existing_daemon: bool,
        farmer_config: Dict[str, Any],
    ):
        self.root_path = root_path
        self.config = config
        self.allow_connecting_to_existing_daemon = allow_connecting_to_existing_daemon
        self._farmer_config = farmer_config

    async def init(self) -> None:
        if self._binary_directory_path is None:
            self._binary_directory_path = await self._binary_manager.get_binary_directory_path()

    async def start_daemon(self) -> None:
        if self._daemon_proxy is not None:
            return
        self._daemon_proxy = await connect_to_daemon_and_validate(self.root_path, self.config, quiet=True)
        if self._daemon_proxy is not None:
            if not self.allow_connecting_to_existing_daemon:
                self._logger.error("Another instance of foxy-farmer is already running, exiting now ..")

                raise AlreadyRunningException

            await ensure_daemon_keyring_is_unlocked(self._daemon_proxy)

            return

        self._chia_daemon_process = self._start_daemon_process()
        if self._chia_daemon_process.stdout:
            self._chia_daemon_process.stdout.readline()
        self._daemon_proxy = await get_daemon_proxy(self.root_path, self.config)
        await ensure_daemon_keyring_is_unlocked(self._daemon_proxy)

    async def stop_daemon(self) -> None:
        if self._chia_daemon_process is not None:
            r = await self._daemon_proxy.exit()
            if r.get("data", {}).get("success", False):
                if r["data"].get("services_stopped") is not None:
                    [print(f"{service}: Stopped") for service in r["data"]["services_stopped"]]
                print("Daemon stopped")
                self._chia_daemon_process = None
            else:
                print(f"Stop daemon failed {r}")
        if self._daemon_proxy is not None:
            await self._daemon_proxy.close()
            self._daemon_proxy = None

    async def start_services(self, service_names: List[str]) -> None:
        if self._daemon_proxy is None:
            raise ValueError("Daemon Proxy not initialized")
        for service in services_for_groups(service_names):
            if await self._daemon_proxy.is_running(service_name=service):
                continue
            print(f"{service}: ", end="", flush=True)
            msg = await self._daemon_proxy.start_service(service_name=service)
            success = msg and msg["data"]["success"]

            if success is True:
                print("started")
            else:
                error = "no response"
                if msg:
                    error = msg["data"]["error"]
                print(f"{service} failed to start. Error: {error}")

    async def stop_services(self, service_names: List[str]) -> None:
        if self._daemon_proxy is None:
            raise ValueError("Daemon Proxy not initialized")
        for service in services_for_groups(service_names):
            if not await self._daemon_proxy.is_running(service_name=service):
                continue
            print(f"{service}: ", end="", flush=True)
            msg = await self._daemon_proxy.stop_service(service_name=service)
            success = msg and msg["data"]["success"]

            if success is True:
                print("stopped")
            else:
                error = "no response"
                if msg:
                    error = msg["data"]["error"]
                print(f"{service} failed to stop. Error: {error}")

    def _start_daemon_process(self) -> Popen:
        os.environ["CHIA_ROOT"] = str(self.root_path)
        if self._farmer_config.get("recompute_hosts") is not None:
            if isinstance(self._farmer_config["recompute_hosts"], str):
                os.environ["CHIAPOS_RECOMPUTE_HOST"] = self._farmer_config["recompute_hosts"]
            elif isinstance(self._farmer_config["recompute_hosts"], list) and len(self._farmer_config["recompute_hosts"]) > 0:
                os.environ["CHIAPOS_RECOMPUTE_HOST"] = ",".join(self._farmer_config["recompute_hosts"])
        if self._farmer_config.get("recompute_connect_timeout") is not None:
            os.environ["CHIAPOS_RECOMPUTE_CONNECT_TIMEOUT"] = str(self._farmer_config["recompute_connect_timeout"])
        if self._farmer_config.get("recompute_retry_interval") is not None:
            os.environ["CHIAPOS_RECOMPUTE_RETRY_INTERVAL"] = str(self._farmer_config["recompute_retry_interval"])
        if self._farmer_config.get("chiapos_max_cores") is not None:
            os.environ["CHIAPOS_MAX_CORES"] = str(self._farmer_config["chiapos_max_cores"])
        if self._farmer_config.get("chiapos_max_cuda_devices") is not None:
            os.environ["CHIAPOS_MAX_CUDA_DEVICES"] = str(self._farmer_config["chiapos_max_cuda_devices"])
        if self._farmer_config.get("chiapos_max_opencl_devices") is not None:
            os.environ["CHIAPOS_MAX_OPENCL_DEVICES"] = str(self._farmer_config["chiapos_max_opencl_devices"])
        if self._farmer_config.get("chiapos_max_gpu_devices") is not None:
            os.environ["CHIAPOS_MAX_GPU_DEVICES"] = str(self._farmer_config["chiapos_max_gpu_devices"])
        if self._farmer_config.get("chiapos_opencl_platform") is not None:
            os.environ["CHIAPOS_OPENCL_PLATFORM"] = str(self._farmer_config["chiapos_opencl_platform"])
        if self._farmer_config.get("chiapos_min_gpu_log_entries") is not None:
            os.environ["CHIAPOS_MIN_GPU_LOG_ENTRIES"] = str(self._farmer_config["chiapos_min_gpu_log_entries"])
        if self._farmer_config.get("cuda_visible_devices") is not None:
            os.environ["CUDA_VISIBLE_DEVICES"] = str(self._farmer_config["cuda_visible_devices"])

        creationflags = 0
        chia_binary_name = "chia.bin"
        if platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW
            chia_binary_name = "chia.exe"

        process = subprocess.Popen(
            [join(self._binary_directory_path, chia_binary_name), "run_daemon", "--wait-for-unlock"],
            encoding="utf-8",
            cwd=self._binary_directory_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
        )

        return process

