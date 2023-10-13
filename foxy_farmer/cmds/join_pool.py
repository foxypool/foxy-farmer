import asyncio
import functools
import time
from asyncio import sleep, create_task
from pathlib import Path
from typing import Dict, Any, List, Optional

import click
from chia.cmds.cmds_util import get_any_service_client, get_wallet
from chia.cmds.plotnft_funcs import submit_tx_with_confirmation
from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.server.outbound_message import NodeType
from chia.server.start_service import Service
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.byte_types import hexstr_to_bytes
from chia.util.chia_logging import initialize_logging
from chia.util.config import load_config
from chia.util.ints import uint64
from chia.wallet.util.wallet_types import WalletType
from chia.wallet.wallet_node import WalletNode
from chia.wallet.wallet_node_api import WalletNodeAPI
from yaspin import yaspin

from foxy_farmer.chia_launcher import ChiaLauncher
from foxy_farmer.pool.pool_api_client import POOL_URL, PoolApiClient
from foxy_farmer.service_factory import ServiceFactory


@click.command("join-pool", short_help="Join your PlotNFTs to the pool")
@click.pass_context
def join_pool_cmd(ctx) -> None:
    foxy_root: Path = ctx.obj["root_path"]
    if not foxy_root.exists():
        print("No config found, please start foxy-farmer at least once before joining the pool!")

        return

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
        await self._chia_launcher.wait_for_ready()

        with yaspin(text="Waiting for the wallet to finish starting ..."):
            await sleep(5)

        async with get_any_service_client(WalletRpcClient, root_path=self._foxy_root) as (wallet_client, _):
            assert wallet_client is not None

            fingerprint = await get_wallet(self._foxy_root, wallet_client, fingerprint=None)

            await wait_for_wallet_sync(wallet_client)

            config = load_config(self._foxy_root, "config.yaml")
            plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(config)
            if len(plot_nfts_not_pooling_with_foxy) == 0:
                print("✅ All PlotNFTs are already pooling with Foxy, nothing to do")
                self.stop()
                await launch_task
                time.sleep(0.1)

                return

            await join_plot_nfts_to_pool(wallet_client, plot_nfts_not_pooling_with_foxy, fingerprint)

            await wait_for_wallet_sync(wallet_client)

            with yaspin(text="Waiting for the pool join to complete ..."):
                while len(plot_nfts_not_pooling_with_foxy) > 0:
                    await sleep(15)
                    config = load_config(self._foxy_root, "config.yaml")
                    plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(config)
            print("✅ Pool join completed")

        self.stop()
        await launch_task
        time.sleep(0.1)

    async def start_and_await_services(self):
        service_factory = ServiceFactory(self._foxy_root, self._config)
        self._wallet_service = service_factory.make_wallet()

        awaitables = [
            self._wallet_service.run(),
            self._chia_launcher.daemon_ws_server.shutdown_event.wait(),
        ]

        await asyncio.gather(*awaitables)

    def stop(self):
        self._wallet_service.stop()
        asyncio.create_task(self._chia_launcher.daemon_ws_server.stop())


async def join_plot_nfts_to_pool(wallet_client: WalletRpcClient, plot_nfts: List[Dict[str, Any]], fingerprint: int):
    plot_nfts_by_launcher_id: Dict[bytes32, Dict[str, Any]] = {
        bytes32.from_hexstr(plot_nft["launcher_id"]): plot_nft
        for plot_nft in plot_nfts
    }

    pool_api_client = PoolApiClient()
    with yaspin(text="Fetching latest pool info ..."):
        pool_info = await pool_api_client.get_pool_info()

    with yaspin(text="Fetching PlotNFT wallets ..."):
        pooling_wallets = await wallet_client.get_wallets(wallet_type=WalletType.POOLING_WALLET)
    for pool_wallet in pooling_wallets:
        wallet_id = pool_wallet["id"]
        pool_wallet_info, _ = await wallet_client.pw_status(wallet_id)
        plot_nft = plot_nfts_by_launcher_id.get(pool_wallet_info.launcher_id)
        if plot_nft is None:
            print(f"Could not find PlotNFT for LauncherID {pool_wallet_info.launcher_id.hex()} in config.yaml, skipping")
            continue
        with yaspin(text=f"Joining PlotNFT with LauncherID {pool_wallet_info.launcher_id.hex()} to the pool ..."):
            await join_plot_nft_to_pool(wallet_client, pool_info, wallet_id, fingerprint)


async def join_plot_nft_to_pool(wallet_client: WalletRpcClient, pool_info: Dict[str, Any], wallet_id: int, fingerprint: int):
    func = functools.partial(
        wallet_client.pw_join_pool,
        wallet_id,
        hexstr_to_bytes(pool_info["target_puzzle_hash"]),
        POOL_URL,
        pool_info["relative_lock_height"],
        uint64(0),
    )
    await submit_tx_with_confirmation("", False, func, wallet_client, fingerprint, wallet_id)
    await sleep(15)


async def wait_for_wallet_sync(wallet_client: WalletRpcClient):
    with yaspin(text="Waiting for the wallet to sync ..."):
        while len(await wallet_client.get_connections(node_type=NodeType.FULL_NODE)) < 2:
            await sleep(5)
        await sleep(10)
        while await wallet_client.get_sync_status():
            await sleep(5)
        while not (await wallet_client.get_synced()):
            await sleep(5)
    print("✅ Wallet synced")


def get_plot_nft_not_pooling_with_foxy(config: Dict[str, Any]) -> List[Dict[str, Any]]:
    if config["pool"].get("pool_list") is None:
        return []

    return list(filter(lambda pool: "foxypool.io" not in pool["pool_url"], config["pool"]["pool_list"]))
