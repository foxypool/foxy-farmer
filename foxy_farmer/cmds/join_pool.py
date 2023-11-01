import asyncio
import functools
import time
from asyncio import sleep, create_task
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Optional, Callable, Awaitable

import click
from chia.cmds.cmds_util import get_wallet
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.server.outbound_message import NodeType
from chia.server.start_service import Service
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.byte_types import hexstr_to_bytes
from chia.util.chia_logging import initialize_logging
from chia.util.config import load_config
from chia.util.ints import uint64, uint16
from chia.wallet.transaction_record import TransactionRecord
from chia.wallet.util.wallet_types import WalletType
from chia.wallet.wallet_node import WalletNode
from chia.wallet.wallet_node_api import WalletNodeAPI
from humanize import naturaldelta
from yaspin import yaspin

from foxy_farmer.chia_launcher import ChiaLauncher
from foxy_farmer.error_reporting import close_sentry
from foxy_farmer.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_farmer.pool.pool_api_client import POOL_URL, PoolApiClient
from foxy_farmer.service_factory import ServiceFactory
from foxy_farmer.util.hex import ensure_hex_prefix


@click.command("join-pool", short_help="Join your PlotNFTs to the pool")
@click.pass_context
def join_pool_cmd(ctx) -> None:
    foxy_root: Path = ctx.obj["root_path"]
    config_path: Path = ctx.obj["config_path"]
    foxy_chia_config_manager = FoxyChiaConfigManager(foxy_root)
    foxy_chia_config_manager.ensure_foxy_config(config_path)

    config = load_config(foxy_root, "config.yaml")

    initialize_logging(
        service_name="foxy_farmer",
        logging_config=config["logging"],
        root_path=foxy_root,
    )

    asyncio.run(join_pool(foxy_root, config))


async def join_pool(foxy_root: Path, config: Dict[str, Any]):
    pool_joiner = PoolJoiner(foxy_root=foxy_root, config=config)
    await pool_joiner.join_pool()


class PoolJoiner:
    _foxy_root: Path
    _config: Dict[str, Any]
    _wallet_service: Optional[Service[WalletNode, WalletNodeAPI]]
    _chia_launcher: Optional[ChiaLauncher]

    def __init__(self, foxy_root: Path, config: Dict[str, Any]):
        self._foxy_root = foxy_root
        self._config = config

    async def join_pool(self):
        self._chia_launcher = ChiaLauncher(foxy_root=self._foxy_root, config=self._config)
        launch_task = create_task(self._chia_launcher.run_with_daemon(self.start_and_await_services))
        await self._chia_launcher.wait_for_ready_or_shutdown()
        if self._chia_launcher.is_shut_down:
            await launch_task

            return

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
        finally:
            wallet_rpc.close()
            await wallet_rpc.await_closed()
            self.stop()
            await launch_task
            time.sleep(0.1)
            close_sentry()

    async def start_and_await_services(self):
        service_factory = ServiceFactory(self._foxy_root, self._config)
        self._wallet_service = service_factory.make_wallet()

        awaitables = [
            self._wallet_service.run(),
        ]

        await asyncio.gather(*awaitables)

    def stop(self):
        self._wallet_service.stop()


async def await_launcher_pool_join_completion(root_path: Path, joined_launcher_ids: List[str]):
    plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(root_path, joined_launcher_ids=joined_launcher_ids)
    if len(plot_nfts_not_pooling_with_foxy) == 0:
        return
    with yaspin(text="Waiting for the pool join to complete ..."):
        while len(plot_nfts_not_pooling_with_foxy) > 0:
            await sleep(15)
            plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(root_path, joined_launcher_ids=joined_launcher_ids)


async def join_plot_nfts_to_pool(wallet_client: WalletRpcClient, plot_nfts: List[Dict[str, Any]]) -> List[str]:
    plot_nfts_by_launcher_id: Dict[bytes32, Dict[str, Any]] = {
        bytes32.from_hexstr(plot_nft["launcher_id"]): plot_nft
        for plot_nft in plot_nfts
    }

    pool_api_client = PoolApiClient()
    with yaspin(text="Fetching latest pool info ..."):
        pool_info = await pool_api_client.get_pool_info()

    with yaspin(text="Fetching PlotNFT wallets ..."):
        pooling_wallets = await wallet_client.get_wallets(wallet_type=WalletType.POOLING_WALLET)
    joined_launcher_ids: List[str] = []
    for pool_wallet in pooling_wallets:
        wallet_id = pool_wallet["id"]
        pool_wallet_info, _ = await wallet_client.pw_status(wallet_id)
        plot_nft = plot_nfts_by_launcher_id.get(pool_wallet_info.launcher_id)
        launcher_id = pool_wallet_info.launcher_id.hex()
        if plot_nft is None:
            print(f"❌ Could not find PlotNFT with LauncherID {launcher_id} in config.yaml, skipping")

            continue
        with yaspin(text=f"Joining PlotNFT with LauncherID {launcher_id} to the pool ...") as spinner:
            while not (await wallet_client.get_synced()):
                await sleep(5)
            try:
                await join_plot_nft_to_pool(wallet_client, pool_info, wallet_id)
                spinner.stop()
                print(f"✅ Submitted the pool join transaction for PlotNFT with LauncherID {launcher_id}")
                joined_launcher_ids.append(ensure_hex_prefix(launcher_id))
            except Exception as e:
                spinner.stop()
                print(f"❌ Could not join PlotNFT with LauncherID {launcher_id} because an error occurred: {e}")

    return joined_launcher_ids


async def join_plot_nft_to_pool(wallet_client: WalletRpcClient, pool_info: Dict[str, Any], wallet_id: int):
    func = functools.partial(
        wallet_client.pw_join_pool,
        wallet_id,
        hexstr_to_bytes(pool_info["target_puzzle_hash"]),
        POOL_URL,
        pool_info["relative_lock_height"],
        uint64(0),
    )
    await submit_tx_with_confirmation(func, wallet_client)
    await sleep(15)


async def wait_for_wallet_sync(wallet_client: WalletRpcClient):
    with yaspin(text="Waiting for the wallet to sync ...") as spinner:
        async def update_spinner_text():
            connected_full_nodes_count = len(await wallet_client.get_connections(node_type=NodeType.FULL_NODE))
            wallet_height = await wallet_client.get_height_info()
            relative_time = "N/A"
            if connected_full_nodes_count > 0:
                try:
                    wallet_timestamp = await wallet_client.get_timestamp_for_height(wallet_height)
                    relative_time = naturaldelta(datetime.now() - datetime.fromtimestamp(float(wallet_timestamp)))
                except:
                    pass
                spinner.text = f"Waiting for the wallet to sync (peers={connected_full_nodes_count}, height={wallet_height}, {relative_time} behind) ..."

        while len(await wallet_client.get_connections(node_type=NodeType.FULL_NODE)) < 2:
            await update_spinner_text()
            await sleep(5)
        await update_spinner_text()
        await sleep(10)
        while await wallet_client.get_sync_status():
            await update_spinner_text()
            await sleep(5)
        while not (await wallet_client.get_synced()):
            await update_spinner_text()
            await sleep(5)
    print("✅ Wallet synced")


def get_plot_nft_not_pooling_with_foxy(root_path: Path, joined_launcher_ids: Optional[List[str]] = None) -> List[Dict[str, Any]]:
    config = load_config(root_path, "config.yaml")
    if config["pool"].get("pool_list") is None:
        return []

    return list(
        filter(
            lambda pool: "foxypool.io" not in pool["pool_url"] and (joined_launcher_ids is None or ensure_hex_prefix(pool["launcher_id"]) in joined_launcher_ids),
            config["pool"]["pool_list"],
        )
    )


async def submit_tx_with_confirmation(
        func: Callable[[], Awaitable[Dict[str, Any]]],
        wallet_client: WalletRpcClient,
) -> None:
    result = await func()
    tx_record: TransactionRecord = result["transaction"]
    start = time.time()
    while time.time() - start < 15:
        await asyncio.sleep(0.1)
        tx = await wallet_client.get_transaction(1, tx_record.name)
        if len(tx.sent_to) > 0:
            return None
