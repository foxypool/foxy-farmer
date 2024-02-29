from pathlib import Path
from typing import Dict, Any, Optional

from chia.cmds.cmds_util import get_wallet

from foxy_farmer.config.foxy_config import FoxyConfig
from foxy_farmer.environment.embedded_chia_environment import EmbeddedChiaEnvironment
from foxy_farmer.wallet.pool_join import update_foxy_config_plot_nfts_if_required
from foxy_farmer.wallet.run_wallet import run_wallet
from foxy_farmer.wallet.sync import wait_for_wallet_sync


class PlotNftUpdater:
    _foxy_root: Path
    _config: Dict[str, Any]
    _foxy_config: FoxyConfig
    _chia_environment: Optional[EmbeddedChiaEnvironment]

    def __init__(self, foxy_root: Path, config: Dict[str, Any], foxy_config: FoxyConfig):
        self._foxy_root = foxy_root
        self._config = config
        self._foxy_config = foxy_config

    async def update_plot_nfts(self):
        async with run_wallet(root_path=self._foxy_root, config=self._config) as wallet_rpc:
            # Select wallet to sync
            await get_wallet(self._foxy_root, wallet_rpc, fingerprint=None)
            await wait_for_wallet_sync(wallet_rpc)
        update_foxy_config_plot_nfts_if_required(self._foxy_root, self._foxy_config)
