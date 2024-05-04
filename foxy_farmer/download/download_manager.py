import tarfile
from logging import getLogger
from os.path import join
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Union

from aiohttp import ClientSession, ClientTimeout
from yaspin import yaspin
from yaspin.core import Yaspin

from foxy_farmer.util.ssl_context import ssl_context
from foxy_farmer.util.zip_file_with_permissions import ZipFileWithPermissions


class DownloadManager:
    _logger = getLogger("download_manager")

    async def download_archive_and_extract(
        self,
        file_url: str,
        file_name: str,
        to_path: Union[str, Path],
        file_description: str,
    ):
        with yaspin(f"Preparing to download {file_description} ..") as spinner:
            with TemporaryDirectory() as temp_dir:
                archive_path = join(temp_dir, file_name)
                await self.download_file(
                    file_url=file_url,
                    to_path=archive_path,
                    file_description=file_description,
                    spinner=spinner,
                )
                spinner.text = f"Extracting {file_description} .."
                self._extract_file(archive_path, to_path)
        self._logger.info(f"✅ Downloaded {file_description}")

    async def download_file(self, file_url: str, to_path: Union[str, Path], file_description: str, spinner: Yaspin):
        one_mib_in_bytes = 2 ** 20
        chunk_size = 5 * one_mib_in_bytes
        downloaded_size_mib = 0
        async with ClientSession(timeout=ClientTimeout(total=15 * 60, connect=60)) as client:
            async with client.get(file_url, ssl=ssl_context) as res:
                total_bytes = int(res.headers.get('content-length'))
                total_mib = total_bytes / one_mib_in_bytes
                with open(to_path, 'wb') as fd:
                    async for chunk in res.content.iter_chunked(chunk_size):
                        fd.write(chunk)
                        downloaded_size_mib += len(chunk) / one_mib_in_bytes
                        percentage = (downloaded_size_mib / total_mib) * 100
                        spinner.text = f"Downloading {file_description} ({downloaded_size_mib:.2f}/{total_mib:.2f} MiB, {percentage:.2f}%) .."

    def _extract_file(self, archive_file_path: str, destination_path: Path):
        if archive_file_path.endswith(".zip"):
            with ZipFileWithPermissions(archive_file_path, 'r') as zip_ref:
                zip_ref.extractall(destination_path)

            return
        if archive_file_path.endswith(".tar.gz"):
            file = tarfile.open(archive_file_path)
            file.extractall(destination_path)
            file.close()

            return

        raise RuntimeError(f"Can not extract {archive_file_path}, unsupported extension")
