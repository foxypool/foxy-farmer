import time
from asyncio import create_task, sleep, CancelledError, gather
from pathlib import Path
from typing import Dict, Any, Optional, List

from chia.cmds.cmds_util import get_wallet
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.types.aliases import WalletService
from chia.util.config import load_config
from chia.util.ints import uint16
from yaspin import yaspin

from foxy_farmer.chia_launcher import ChiaLauncher
from foxy_farmer.foundation.wallet.pool_join import get_plot_nft_not_pooling_with_foxy, \
    await_launcher_pool_join_completion, join_plot_nfts_to_pool
from foxy_farmer.foundation.wallet.sync import wait_for_wallet_sync
from foxy_farmer.foxy_config_manager import FoxyConfigManager
from foxy_farmer.service_factory import ServiceFactory
from foxy_farmer.util.awaitable import await_done


class PoolJoiner:
    _foxy_root: Path
    _config: Dict[str, Any]
    _foxy_config_manager: FoxyConfigManager
    _wallet_service: Optional[WalletService]
    _chia_launcher: Optional[ChiaLauncher]

    def __init__(self, foxy_root: Path, config: Dict[str, Any], config_path: Path):
        self._foxy_root = foxy_root
        self._config = config
        self._foxy_config_manager = FoxyConfigManager(config_path)

    async def join_pool(self):
        self._chia_launcher = ChiaLauncher(foxy_root=self._foxy_root, config=self._config)
        await self._chia_launcher.ensure_daemon_running_and_unlocked(require_own_daemon=False)
        start_wallet_task = create_task(self.start_and_await_services())

        wallet_rpc = await WalletRpcClient.create(
            self._config["self_hostname"],
            uint16(self._config["wallet"]["rpc_port"]),
            self._foxy_root,
            self._config,
        )

        async def is_wallet_reachable() -> bool:
            try:
                await wallet_rpc.healthz()

                return True
            except:
                return False

        try:
            with yaspin(text="Waiting for the wallet to finish starting ..."):
                while not await is_wallet_reachable():
                    await sleep(3)

            # Select wallet to sync
            await get_wallet(self._foxy_root, wallet_rpc, fingerprint=None)

            await wait_for_wallet_sync(wallet_rpc)
            self._update_foxy_config_plot_nfts_if_required()

            plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(self._foxy_root)
            if len(plot_nfts_not_pooling_with_foxy) == 0:
                print("✅ All PlotNFTs are already pooling with Foxy, nothing to do")

                return

            joined_launcher_ids = await join_plot_nfts_to_pool(wallet_rpc, plot_nfts_not_pooling_with_foxy)
            if len(joined_launcher_ids) == 0:
                print("❌ Unable to join any of the PlotNFTs, exiting")

                return

            await wait_for_wallet_sync(wallet_rpc)

            await await_launcher_pool_join_completion(self._foxy_root, joined_launcher_ids)
            print("✅ Pool join completed")
            self._update_foxy_config_plot_nfts_if_required()
        finally:
            wallet_rpc.close()
            await wallet_rpc.await_closed()
            self.stop()
            try:
                await start_wallet_task
            except:
                await await_done(self._wallet_service.stop_requested.wait())
            self._chia_launcher.shutdown()
            await self._chia_launcher.await_shutdown()
            time.sleep(0.1)

    async def start_and_await_services(self):
        service_factory = ServiceFactory(self._foxy_root, self._config)
        self._wallet_service = service_factory.make_wallet()

        awaitables = [
            self._wallet_service.run(),
        ]

        await gather(*awaitables)

    def stop(self):
        self._wallet_service.stop_requested.set()

    def _update_foxy_config_plot_nfts_if_required(self):
        config = load_config(self._foxy_root, "config.yaml")
        pool_list: Optional[List[Dict[str, Any]]] = config["pool"].get("pool_list")
        if pool_list is None:
            return
        foxy_config = self._foxy_config_manager.load_config()
        if pool_list == foxy_config.get("plot_nfts"):
            return
        foxy_config["plot_nfts"] = pool_list
        self._foxy_config_manager.save_config(foxy_config)
