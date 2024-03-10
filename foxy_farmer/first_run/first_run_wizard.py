from decimal import Decimal
from logging import getLogger
from pathlib import Path
from sys import stdout, stdin, stderr
from typing import List, Any, Dict

from chia.cmds.cmds_util import get_wallet
from chia.cmds.init_funcs import check_keys
from chia.cmds.keys_funcs import query_and_add_private_key_seed
from chia.cmds.units import units
from chia.daemon.keychain_proxy import KeychainProxy
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.bech32m import encode_puzzle_hash
from chia.util.ints import uint64
from chia.util.keychain import Keychain
from prompt_toolkit.shortcuts import CompleteStyle
from questionary import select, Choice, confirm, text, path, checkbox

from foxy_farmer.config.backend import Backend
from foxy_farmer.config.foxy_config import FoxyConfig
from foxy_farmer.keychain.generate_login_links import generate_login_links
from foxy_farmer.util.bech32_address import is_valid_address
from foxy_farmer.util.fee import is_valid_fee
from foxy_farmer.pool.plot_nft_updater import PlotNftUpdater
from foxy_farmer.pool.pool_joiner import PoolJoiner
from foxy_farmer.wallet.balance import ensure_balance
from foxy_farmer.wallet.pool_join import get_plot_nft_not_pooling_with_foxy, update_foxy_config_plot_nfts_if_required, \
    create_plot_nft, get_plot_nft_from_config
from foxy_farmer.wallet.run_wallet import run_wallet
from foxy_farmer.wallet.sync import wait_for_wallet_sync


async def run_first_run_wizard(foxy_root: Path, config: Dict[str, Any], foxy_config: FoxyConfig):
    if not stdout.isatty() or not stdin.isatty():
        print("WARNING: No interactive shell available, skipping first run wizard!", file=stderr)

        return
    print("New install detected, running first run wizard")
    use_og_pooling: bool = await confirm(
        message="Do you have OG (SOLO) plots you want to pool with?",
        default=foxy_config["enable_og_pooling"],
    ).unsafe_ask_async()
    foxy_config["enable_og_pooling"] = use_og_pooling

    backend_choices: List[Choice] = [
        Choice(title=f"{Backend.BladeBit} - uncompressed as well as Bladebit compressed plots", value=Backend.BladeBit),
    ]
    if not use_og_pooling:
        backend_choices.extend([
            Choice(title=f"{Backend.Gigahorse} - uncompressed as well as Gigahorse compressed plots", value=Backend.Gigahorse),
            Choice(title=f"{Backend.DrPlotter} - uncompressed as well as DrPlotter compressed plots", value=Backend.DrPlotter),
        ])
    backend: Backend = await select(
        message="Which backend do you want to use?",
        choices=backend_choices,
    ).unsafe_ask_async()
    foxy_config["backend"] = f"{backend}"

    if backend == Backend.DrPlotter:
        dr_plotter_client_token: str = await text(
            message="Please enter your DrPlotter client token:",
            validate=lambda token: len(token.strip()) == 48
        ).unsafe_ask_async()
        foxy_config["dr_plotter_client_token"] = dr_plotter_client_token.strip()

    payout_address: str = await text(
        message="Which payout address do you want to use?",
        default=foxy_config["pool_payout_address"],
        validate=is_valid_address,
    ).unsafe_ask_async()
    foxy_config["pool_payout_address"] = payout_address

    farmer_reward_address: str = await text(
        message="Which farmer reward address do you want to use?",
        default=foxy_config["pool_payout_address"],
        validate=is_valid_address,
    ).unsafe_ask_async()
    foxy_config["farmer_reward_address"] = farmer_reward_address

    existing_plot_directories: List[str] = foxy_config["plot_directories"]
    if len(existing_plot_directories) > 0:
        existing_plot_directories = await checkbox(
            message="Keep these already configured plot directories?",
            choices=list(map(lambda plot_dir: Choice(title=plot_dir, checked=True), existing_plot_directories)),
        ).unsafe_ask_async()

    use_recursive_plot_scan: bool = await confirm(
        message="Enable recursive plot scan?",
        default=foxy_config.get("recursive_plot_scan", False),
    ).unsafe_ask_async()
    foxy_config["recursive_plot_scan"] = use_recursive_plot_scan

    while True:
        plot_directory_raw: str = await path(
            message="Add a plot directory path, leave empty to continue with the setup",
            validate=lambda plot_dir: Path(plot_dir).exists(),
            only_directories=True,
            complete_style=CompleteStyle.READLINE_LIKE,
        ).unsafe_ask_async()
        plot_directory = plot_directory_raw.strip()
        if plot_directory == "":
            break
        existing_plot_directories.append(plot_directory)

    keychain = Keychain()
    all_sks = keychain.get_all_private_keys()
    if len(all_sks) == 0:
        should_add_keys: bool = await confirm(
            message="No keys found on this system, add a mnemonic now?",
            default=True,
        ).unsafe_ask_async()
        if should_add_keys:
            while len(all_sks) == 0:
                query_and_add_private_key_seed(mnemonic=None)
                check_keys(foxy_root)
                all_sks = keychain.get_all_private_keys()

    has_plot_nfts = len(foxy_config["plot_nfts"]) > 0
    should_sync_wallet_message = "No PlotNFTs detected, do you want to sync the wallet to auto fill them?"
    if has_plot_nfts:
        should_sync_wallet_message = "Do you want to sync the wallet to update your PlotNFT states?"
    should_sync_wallet: bool = await confirm(
        message=should_sync_wallet_message,
        default=not has_plot_nfts,
    ).unsafe_ask_async()
    if should_sync_wallet:
        plot_nft_updater = PlotNftUpdater(foxy_root=foxy_root, config=config, foxy_config=foxy_config)
        await plot_nft_updater.update_plot_nfts()
        plot_nft_count = len(foxy_config["plot_nfts"])
        if plot_nft_count == 0:
            print("No PlotNFTs found, skipping ..")
        else:
            print(
                f"{'Updated' if has_plot_nfts else 'Found'} {plot_nft_count} PlotNFT{'s' if plot_nft_count > 1 else ''}")

    if len(foxy_config["plot_nfts"]) == 0 and len(all_sks) > 0:
        should_create_plot_nft: bool = await confirm(
            message="No PlotNFTs found, do you want to create a new PlotNFT?",
            default=True,
        ).unsafe_ask_async()
        if should_create_plot_nft:
            await create_plot_nft_interactive(foxy_root, config, foxy_config, )

    if len(foxy_config["plot_nfts"]) > 0 and len(all_sks) > 0:
        plot_nfts_not_pooling_with_foxy = get_plot_nft_not_pooling_with_foxy(foxy_root)
        if len(plot_nfts_not_pooling_with_foxy) > 0:
            should_join_pool: bool = await confirm(
                message="Do you want to join your PlotNFTs to Foxy-Pool?",
                default=True,
            ).unsafe_ask_async()
            if should_join_pool:
                fee_str: str = await text(
                    message="Which fee (in XCH) do you want to use?",
                    default="0",
                    validate=is_valid_fee,
                ).unsafe_ask_async()
                fee_raw: uint64 = uint64(int(Decimal(fee_str) * units["chia"]))
                pool_joiner = PoolJoiner(foxy_root=foxy_root, config=config, foxy_config=foxy_config)
                await pool_joiner.join_pool(fee=fee_raw)

        should_print_login_links: bool = await confirm(
            message="Show the login links of your PlotNFTs?",
            default=True,
        ).unsafe_ask_async()
        if should_print_login_links:
            login_links = await generate_login_links(
                KeychainProxy(log=getLogger("first_run_wizard"), local_keychain=keychain),
                foxy_config["plot_nfts"],
            )
            print("Login links for your PlotNFTs:")
            for launcher_id, login_link in login_links:
                print()
                print(f"Launcher ID: {launcher_id}")
                print(f" Login Link: {login_link}")
            print()


async def create_plot_nft_interactive(foxy_root: Path, config: Dict[str, Any], foxy_config: FoxyConfig):
    fee_str: str = await text(
        message="Which fee (in XCH) do you want to use?",
        default="0",
        validate=is_valid_fee,
    ).unsafe_ask_async()
    fee_raw: uint64 = uint64(int(Decimal(fee_str) * units["chia"]))
    async with run_wallet(root_path=foxy_root, config=config) as wallet_rpc:
        # Select wallet to sync
        await get_wallet(foxy_root, wallet_rpc, fingerprint=None)
        await wait_for_wallet_sync(wallet_rpc)
        wallet_address = await wallet_rpc.get_next_address(1, new_address=False)

        await ensure_balance(
            wallet_client=wallet_rpc,
            required_balance_mojo=fee_raw + 1,
            message_while_waiting_closure=lambda remaining_xch: f"Not enough XCH available to create PlotNFT, please send at least {remaining_xch} XCH to {wallet_address}",
        )

        launcher_id = await create_plot_nft(wallet_rpc, fee=fee_raw)
        if launcher_id is None:
            return
        await wait_for_wallet_sync(wallet_rpc)
        update_foxy_config_plot_nfts_if_required(foxy_root, foxy_config)
        plot_nft = get_plot_nft_from_config(foxy_root, launcher_id)
        if plot_nft is None:
            return
        pool_contract_address = encode_puzzle_hash(
            puzzle_hash=bytes32.from_hexstr(plot_nft['p2_singleton_puzzle_hash']),
            prefix="xch",
        )
        print("!! Please make note of the Launcher ID and Pool Contract Address below !!")
        print()
        print(f"          Launcher ID: {launcher_id}")
        print(f"Pool Contract Address: {pool_contract_address}")
        print()
