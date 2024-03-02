import tarfile
from abc import ABC
from logging import getLogger
from os.path import expanduser, join
from pathlib import Path
from ssl import SSLContext
from sys import platform
from tempfile import TemporaryDirectory
from typing import List
from zipfile import ZipFile

from aiohttp import ClientSession, ClientTimeout
from chia.server.server import ssl_context_for_root
from chia.ssl.create_ssl import get_mozilla_ca_crt
from yaspin import yaspin
from yaspin.core import Yaspin


class BinaryManager(ABC):
    @property
    def binary_name(self) -> str:
        if platform == "win32":
            return "chia.exe"

        return "chia"

    @property
    def _product_name(self) -> str:
        ...

    @property
    def _binary_release(self) -> str:
        ...

    @property
    def _release_download_url(self) -> str:
        ...

    @property
    def _archive_file_name(self) -> str:
        ...

    @property
    def _binary_sub_directory_paths(self) -> List[str]:
        return []

    _cache_path: Path = Path(expanduser("~/.foxy-farmer/bin-cache")).resolve()
    _ssl_context: SSLContext = ssl_context_for_root(get_mozilla_ca_crt())
    _logger = getLogger("binary_manager")

    async def get_binary_directory_path(self) -> Path:
        product_cache_base_path = Path(join(self._cache_path, self._product_name.lower()))
        cache_base_path = Path(join(product_cache_base_path, self._binary_release))
        binary_directory_path = Path(join(cache_base_path, *self._binary_sub_directory_paths))
        if binary_directory_path.exists():
            return binary_directory_path

        with yaspin(text=f"Preparing to download {self._product_name} {self._binary_release} ..") as spinner:
            product_cache_base_path.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory() as temp_dir:
                archive_path = join(temp_dir, self._archive_file_name)
                await self._download_release(archive_path, spinner=spinner)
                spinner.text = f"Extracting {self._product_name} {self._binary_release} .."
                self._extract_file(archive_path, cache_base_path)
        self._logger.info(f"✅ Downloaded {self._product_name} {self._binary_release}")

        return binary_directory_path

    def _extract_file(self, archive_file_path: str, destination_path: Path):
        if archive_file_path.endswith(".zip"):
            with ZipFile(archive_file_path, 'r') as zip_ref:
                zip_ref.extractall(destination_path)

            return
        if archive_file_path.endswith(".tar.gz"):
            file = tarfile.open(archive_file_path)
            file.extractall(destination_path)
            file.close()

            return

        raise RuntimeError(f"Can not extract {archive_file_path}, unsupported extension")

    async def _download_release(self, to_path: str, spinner: Yaspin):
        one_mib_in_bytes = 2 ** 20
        chunk_size = 5 * one_mib_in_bytes
        downloaded_size_mib = 0
        async with ClientSession(timeout=ClientTimeout(total=15 * 60, connect=60)) as client:
            async with client.get(self._release_download_url, ssl=self._ssl_context) as res:
                total_bytes = int(res.headers.get('content-length'))
                total_mib = total_bytes / one_mib_in_bytes
                with open(to_path, 'wb') as fd:
                    async for chunk in res.content.iter_chunked(chunk_size):
                        fd.write(chunk)
                        downloaded_size_mib += len(chunk) / one_mib_in_bytes
                        percentage = (downloaded_size_mib / total_mib) * 100
                        spinner.text = f"Downloading {self._product_name} {self._binary_release} ({downloaded_size_mib:.2f}/{total_mib:.2f} MiB, {percentage:.2f}%) .."

