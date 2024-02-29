from pathlib import Path
from typing import Dict, Any, Optional

from chia.cmds.cmds_util import get_wallet
from chia.util.ints import uint64

from foxy_farmer.environment import EmbeddedChiaEnvironment
from foxy_farmer.wallet.pool_join import get_plot_nft_not_pooling_with_foxy, \
    await_launcher_pool_join_completion, join_plot_nfts_to_pool, update_foxy_config_plot_nfts_if_required
from foxy_farmer.wallet.sync import wait_for_wallet_sync
from foxy_farmer.wallet.run_wallet import run_wallet


class PoolJoiner:
    _foxy_root: Path
    _config: Dict[str, Any]
    _foxy_config: Dict[str, Any]
    _chia_environment: Optional[EmbeddedChiaEnvironment]

    def __init__(self, foxy_root: Path, config: Dict[str, Any], foxy_config: Dict[str, Any]):
        self._foxy_root = foxy_root
        self._config = config
        self._foxy_config = foxy_config

    async def join_pool(self, fee: uint64) -> bool:
        did_update = False
        async with run_wallet(root_path=self._foxy_root, config=self._config) as wallet_rpc:
            # Select wallet to sync
            await get_wallet(self._foxy_root, wallet_rpc, fingerprint=None)

            await wait_for_wallet_sync(wallet_rpc)
            did_update = update_foxy_config_plot_nfts_if_required(self._foxy_root, self._foxy_config)

            plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(self._foxy_root)
            if len(plot_nfts_not_pooling_with_foxy) == 0:
                print("✅ All PlotNFTs are already pooling with Foxy, nothing to do")

                return did_update

            joined_launcher_ids = await join_plot_nfts_to_pool(wallet_rpc, plot_nfts_not_pooling_with_foxy, fee=fee)
            if len(joined_launcher_ids) == 0:
                print("❌ Unable to join any of the PlotNFTs, exiting")

                return did_update

            await wait_for_wallet_sync(wallet_rpc)

            await await_launcher_pool_join_completion(self._foxy_root, joined_launcher_ids)
        print("✅ Pool join completed")
        did_update_again = update_foxy_config_plot_nfts_if_required(self._foxy_root, self._foxy_config)

        return did_update or did_update_again
