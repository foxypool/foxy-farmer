from asyncio import sleep
from pathlib import Path
from typing import List, Optional, Dict

from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.byte_types import hexstr_to_bytes
from chia.util.config import load_config
from chia.util.ints import uint64
from chia.wallet.util.wallet_types import WalletType
from yaspin import yaspin

from foxy_farmer.config.foxy_config import PlotNft, FoxyConfig
from foxy_farmer.pool.pool_api_client import PoolApiClient, POOL_URL
from foxy_farmer.util.hex import ensure_hex_prefix
from foxy_farmer.wallet.transaction import await_transaction_broadcasted


async def join_plot_nfts_to_pool(wallet_client: WalletRpcClient, plot_nfts: List[PlotNft], fee: uint64 = uint64(0)) -> List[str]:
    plot_nfts_by_launcher_id: Dict[bytes32, PlotNft] = {
        bytes32.from_hexstr(plot_nft["launcher_id"]): plot_nft
        for plot_nft in plot_nfts
    }

    pool_api_client = PoolApiClient()
    with yaspin(text="Fetching latest pool info ..."):
        pool_info = await pool_api_client.get_pool_info()

    with yaspin(text="Fetching PlotNFT wallets ..."):
        pooling_wallets = await wallet_client.get_wallets(wallet_type=WalletType.POOLING_WALLET)

    async def join_plot_nft_to_pool(wallet_id_to_join: int):
        join_pool_coro = wallet_client.pw_join_pool(
            wallet_id_to_join,
            bytes32(hexstr_to_bytes(pool_info["target_puzzle_hash"])),
            POOL_URL,
            pool_info["relative_lock_height"],
            fee,
        )
        await await_transaction_broadcasted(join_pool_coro, wallet_client)
        await sleep(15)

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
                await join_plot_nft_to_pool(wallet_id)
                spinner.stop()
                print(f"✅ Submitted the pool join transaction for PlotNFT with LauncherID {launcher_id}")
                joined_launcher_ids.append(ensure_hex_prefix(launcher_id))
            except Exception as e:
                spinner.stop()
                print(f"❌ Could not join PlotNFT with LauncherID {launcher_id} because an error occurred: {e}")

    return joined_launcher_ids


async def await_launcher_pool_join_completion(root_path: Path, joined_launcher_ids: List[str]):
    plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(root_path, joined_launcher_ids=joined_launcher_ids)
    if len(plot_nfts_not_pooling_with_foxy) == 0:
        return
    with yaspin(text="Waiting for the pool join to complete ..."):
        while len(plot_nfts_not_pooling_with_foxy) > 0:
            await sleep(15)
            plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(root_path, joined_launcher_ids=joined_launcher_ids)


def get_plot_nft_not_pooling_with_foxy(root_path: Path, joined_launcher_ids: Optional[List[str]] = None) -> List[PlotNft]:
    config = load_config(root_path, "config.yaml")
    if config["pool"].get("pool_list") is None:
        return []

    return list(
        filter(
            lambda pool: "foxypool.io" not in pool["pool_url"] and (joined_launcher_ids is None or ensure_hex_prefix(pool["launcher_id"]) in joined_launcher_ids),
            config["pool"]["pool_list"],
        )
    )


def update_foxy_config_plot_nfts_if_required(root_path: Path, foxy_config: FoxyConfig) -> bool:
    config = load_config(root_path, "config.yaml")
    pool_list: Optional[List[PlotNft]] = config["pool"].get("pool_list")
    if pool_list is None:
        return False
    if pool_list == foxy_config.get("plot_nfts"):
        return False
    foxy_config["plot_nfts"] = pool_list

    return True
