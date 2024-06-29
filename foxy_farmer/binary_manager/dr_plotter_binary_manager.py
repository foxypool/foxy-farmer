from sys import platform
from typing import List


from foxy_farmer.binary_manager.binary_manager import BinaryManager

dr_plotter_binary_release = "1.0.4"


class DrPlotterBinaryManager(BinaryManager):
    @property
    def binary_name(self) -> str:
        if platform == "win32":
            return "drchia.exe"

        return "drchia"

    @property
    def _product_name(self) -> str:
        return "DrPlotter"

    @property
    def _binary_release(self) -> str:
        return dr_plotter_binary_release

    @property
    def _release_download_url(self) -> str:
        return f"https://downloads.foxypool.io/chia/drplotter/{self._binary_release}/{self._archive_file_name}"

    @property
    def _archive_file_name(self) -> str:
        archive_base = f"drplotter-{self._binary_release}"

        return f"{archive_base}-x86_64.tar.gz"

    @property
    def _binary_sub_directory_paths(self) -> List[str]:
        return [f"drplotter-{self._binary_release}-x86_64", "drharvester"]
