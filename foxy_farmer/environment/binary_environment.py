import subprocess
from abc import ABC
from os.path import join
from pathlib import Path
from signal import CTRL_C_EVENT
from subprocess import Popen
from sys import platform
from typing import Optional, List

from foxy_farmer.binary_manager.binary_manager import BinaryManager


class BinaryEnvironment(ABC):
    @property
    def process_arguments(self) -> List[str]:
        ...

    _binary_manager: BinaryManager
    _binary_directory_path: Optional[Path] = None
    _process: Optional[Popen] = None

    async def init(self) -> None:
        if self._binary_directory_path is None:
            self._binary_directory_path = await self._binary_manager.get_binary_directory_path()

    async def start(self) -> None:
        if self._process is not None:
            return
        self._process = self._start_process()

    async def stop(self) -> None:
        if self._process is not None:
            self._process.send_signal(CTRL_C_EVENT)
            self._process.wait()
            self._process = None

    def _start_process(self) -> Popen:
        creationflags = 0
        if platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW

        process = subprocess.Popen(
            [join(self._binary_directory_path, self._binary_manager.binary_name), *self.process_arguments],
            encoding="utf-8",
            cwd=self._binary_directory_path,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            creationflags=creationflags,
        )

        return process
