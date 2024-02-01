import os
from logging import getLogger
from pathlib import Path
from subprocess import Popen
from sys import platform
from typing import Any, Dict

from foxy_farmer.binary_manager.gigahorse_binary_manager import GigahorseBinaryManager
from foxy_farmer.farmer.binary_chia_environment import BinaryChiaEnvironment


class GigahorseChiaEnvironment(BinaryChiaEnvironment):
    @property
    def chia_binary_name(self) -> str:
        if platform == "win32":
            return "chia.exe"

        return "chia.bin"

    def __init__(
        self,
        root_path: Path,
        config: Dict[str, Any],
        allow_connecting_to_existing_daemon: bool,
        farmer_config: Dict[str, Any],
    ):
        self._logger = getLogger("gigahorse_chia_environment")
        self._binary_manager = GigahorseBinaryManager()
        super().__init__(root_path, config, allow_connecting_to_existing_daemon, farmer_config)

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

        return super()._start_daemon_process()

