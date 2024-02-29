from asyncio import get_running_loop, sleep
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import Dict, Any

from chia.cmds.passphrase_funcs import get_current_passphrase
from chia.daemon.client import DaemonProxy, connect_to_daemon_and_validate
from chia.util.keychain import Keychain


async def get_unlocked_daemon_proxy(
    root_path: Path,
    chia_config: Dict[str, Any],
) -> DaemonProxy:
    daemon_proxy = await get_daemon_proxy(root_path, chia_config)
    await ensure_daemon_keyring_is_unlocked(daemon_proxy)

    return daemon_proxy


async def get_daemon_proxy(root_path: Path, chia_config: Dict[str, Any]) -> DaemonProxy:
    daemon_proxy = await connect_to_daemon_and_validate(root_path, chia_config, quiet=True)
    while daemon_proxy is None:
        await sleep(1)
        daemon_proxy = await connect_to_daemon_and_validate(root_path, chia_config, quiet=True)

    return daemon_proxy


async def ensure_daemon_keyring_is_unlocked(daemon_proxy: DaemonProxy):
    if await daemon_proxy.is_keyring_locked():
        passphrase = Keychain.get_cached_master_passphrase()
        if passphrase is None or not Keychain.master_passphrase_is_valid(passphrase):
            with ThreadPoolExecutor(max_workers=1, thread_name_prefix="get_current_passphrase") as executor:
                passphrase = await get_running_loop().run_in_executor(executor, get_current_passphrase)

        if passphrase:
            print("Unlocking daemon keyring")
            await daemon_proxy.unlock_keyring(passphrase)
