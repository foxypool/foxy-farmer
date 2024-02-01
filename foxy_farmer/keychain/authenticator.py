from logging import getLogger
from pathlib import Path
from typing import Dict, Any, Optional

from chia.daemon.keychain_proxy import KeychainProxy, connect_to_keychain_and_validate

from foxy_farmer.farmer.embedded_chia_environment import EmbeddedChiaEnvironment
from foxy_farmer.foundation.keychain.generate_login_links import generate_login_links


class Authenticator:
    _foxy_root: Path
    _config: Dict[str, Any]
    _chia_environment: Optional[EmbeddedChiaEnvironment]

    def __init__(self, foxy_root: Path, config: Dict[str, Any]):
        self._foxy_root = foxy_root
        self._config = config

    async def authenticate(self):
        pool_list = self._config["pool"].get("pool_list", [])
        if len(pool_list) == 0:
            print("No PlotNFTs found in your config, did you join the pool via the join-pool command yet?")

            return

        self._chia_environment = EmbeddedChiaEnvironment(
            root_path=self._foxy_root,
            config=self._config,
            allow_connecting_to_existing_daemon=True,
        )
        await self._chia_environment.start_daemon()
        logger = getLogger("auth")
        keychain_proxy: Optional[KeychainProxy] = None
        try:
            keychain_proxy = await connect_to_keychain_and_validate(self._foxy_root, logger)
            assert keychain_proxy is not None
            login_links = await generate_login_links(keychain_proxy, pool_list)
            for launcher_id, login_link in login_links:
                print()
                print(f"Launcher Id: {launcher_id}")
                print(f" Login Link: {login_link}")
        finally:
            if keychain_proxy is not None:
                await keychain_proxy.close()
            await self._chia_environment.stop_daemon()
