from platform import machine
from sys import platform
from typing import List


from foxy_farmer.binary_manager.binary_manager import BinaryManager


class GigahorseBinaryManager(BinaryManager):
    @property
    def binary_name(self) -> str:
        if platform == "win32":
            return "chia.exe"

        return "chia.bin"

    @property
    def _product_name(self) -> str:
        return "Gigahorse"

    @property
    def _binary_release(self) -> str:
        return "2.5.3.giga36"

    @property
    def _release_download_url(self) -> str:
        return f"https://downloads.foxypool.io/chia/gigahorse/{self._binary_release}/{self._archive_file_name}"

    @property
    def _archive_file_name(self) -> str:
        archive_base = f"chia-gigahorse-farmer-{self._binary_release}"
        if platform == "win32":
            return f"{archive_base}-windows.zip"
        if machine() == "aarch64":
            return f"{archive_base}-aarch64.tar.gz"

        return f"{archive_base}-x86_64.tar.gz"

    @property
    def _binary_sub_directory_paths(self) -> List[str]:
        return ["chia-gigahorse-farmer"]
