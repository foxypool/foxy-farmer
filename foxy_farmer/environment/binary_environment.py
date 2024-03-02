import subprocess
import sys
from abc import ABC
from asyncio import StreamReader, create_task, Task
from asyncio.subprocess import Process, create_subprocess_exec, PIPE
from os.path import join
from pathlib import Path
from signal import CTRL_BREAK_EVENT
from sys import platform
from typing import Optional, List

from foxy_farmer.binary_manager.binary_manager import BinaryManager


class BinaryEnvironment(ABC):
    @property
    def process_arguments(self) -> List[str]:
        ...

    _binary_manager: BinaryManager
    _binary_directory_path: Optional[Path] = None
    _process: Optional[Process] = None
    _logging_tasks: List[Task] = []

    async def init(self) -> None:
        if self._binary_directory_path is None:
            self._binary_directory_path = await self._binary_manager.get_binary_directory_path()

    async def start(self) -> None:
        if self._process is not None:
            return
        self._process = await self._start_process()

    async def stop(self) -> None:
        if self._process is not None:
            self._process.send_signal(CTRL_BREAK_EVENT)
            await self._process.wait()
            self._process = None
            for task in self._logging_tasks:
                task.cancel()

    async def _start_process(self) -> Process:
        creationflags = 0
        if platform == "win32":
            creationflags = subprocess.CREATE_NEW_PROCESS_GROUP | subprocess.CREATE_NO_WINDOW

        process = await create_subprocess_exec(
            join(self._binary_directory_path, self._binary_manager.binary_name),
            *self.process_arguments,
            cwd=self._binary_directory_path,
            stdout=PIPE,
            stderr=PIPE,
            creationflags=creationflags,
        )
        self._setup_stream_logger(process.stdout, sys.stdout)
        self._setup_stream_logger(process.stderr, sys.stderr)

        return process

    def _setup_stream_logger(self, input_stream: StreamReader, output_stream) -> None:
        async def log_stream():
            while True:
                line = await input_stream.readline()
                if not line:
                    break
                print(line.decode('utf-8'), end='', file=output_stream)

        self._logging_tasks.append(create_task(log_stream()))
