from pathlib import Path
from typing import Dict, Any, Optional

from chia.cmds.cmds_util import get_wallet
from chia.util.ints import uint64

from foxy_farmer.farmer.embedded_chia_environment import EmbeddedChiaEnvironment
from foxy_farmer.foundation.wallet.pool_join import get_plot_nft_not_pooling_with_foxy, \
    await_launcher_pool_join_completion, join_plot_nfts_to_pool, update_foxy_config_plot_nfts_if_required
from foxy_farmer.foundation.wallet.sync import wait_for_wallet_sync
from foxy_farmer.foundation.wallet.run_wallet import run_wallet
from foxy_farmer.foxy_config_manager import FoxyConfigManager


class PoolJoiner:
    _foxy_root: Path
    _config: Dict[str, Any]
    _foxy_config_manager: FoxyConfigManager
    _chia_environment: Optional[EmbeddedChiaEnvironment]

    def __init__(self, foxy_root: Path, config: Dict[str, Any], config_path: Path):
        self._foxy_root = foxy_root
        self._config = config
        self._foxy_config_manager = FoxyConfigManager(config_path)

    async def join_pool(self, fee: uint64):
        async with run_wallet(root_path=self._foxy_root, config=self._config) as wallet_rpc:
            # Select wallet to sync
            await get_wallet(self._foxy_root, wallet_rpc, fingerprint=None)

            await wait_for_wallet_sync(wallet_rpc)
            self._update_foxy_config_plot_nfts_if_required()

            plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(self._foxy_root)
            if len(plot_nfts_not_pooling_with_foxy) == 0:
                print("✅ All PlotNFTs are already pooling with Foxy, nothing to do")

                return

            joined_launcher_ids = await join_plot_nfts_to_pool(wallet_rpc, plot_nfts_not_pooling_with_foxy, fee=fee)
            if len(joined_launcher_ids) == 0:
                print("❌ Unable to join any of the PlotNFTs, exiting")

                return

            await wait_for_wallet_sync(wallet_rpc)

            await await_launcher_pool_join_completion(self._foxy_root, joined_launcher_ids)
        print("✅ Pool join completed")
        self._update_foxy_config_plot_nfts_if_required()

    def _update_foxy_config_plot_nfts_if_required(self):
        foxy_config = self._foxy_config_manager.load_config()
        did_update = update_foxy_config_plot_nfts_if_required(root_path=self._foxy_root, foxy_config=foxy_config)
        if did_update:
            self._foxy_config_manager.save_config(foxy_config)
