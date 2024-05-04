from abc import ABC
from os.path import expanduser, join
from pathlib import Path
from sys import platform
from typing import List

from yaspin import yaspin

from foxy_farmer.download.download_manager import DownloadManager


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
    _download_manager: DownloadManager = DownloadManager()

    async def get_binary_directory_path(self) -> Path:
        product_cache_base_path = Path(join(self._cache_path, self._product_name.lower()))
        cache_base_path = Path(join(product_cache_base_path, self._binary_release))
        binary_directory_path = Path(join(cache_base_path, *self._binary_sub_directory_paths))
        if binary_directory_path.exists():
            return binary_directory_path

        product_cache_base_path.mkdir(parents=True, exist_ok=True)
        file_description = f"{self._product_name} {self._binary_release}"
        await self._download_manager.download_archive_and_extract(
            file_url=self._release_download_url,
            file_name=self._archive_file_name,
            to_path=cache_base_path,
            file_description=file_description,
        )

        return binary_directory_path
