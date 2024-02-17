from logging import getLogger
from pathlib import Path
from sys import stdout, stdin, stderr
from typing import List, Any, Dict

from chia.cmds.init_funcs import check_keys
from chia.cmds.keys_funcs import query_and_add_private_key_seed
from chia.daemon.keychain_proxy import KeychainProxy
from chia.util.keychain import Keychain
from prompt_toolkit.shortcuts import CompleteStyle
from questionary import select, Choice, confirm, text, path, checkbox

from foxy_farmer.foundation.config.backend import Backend
from foxy_farmer.foundation.keychain.generate_login_links import generate_login_links
from foxy_farmer.foundation.util.bech32_address import is_valid_address
from foxy_farmer.pool.plot_nft_updater import PlotNftUpdater


async def run_first_run_wizard(foxy_root: Path, config: Dict[str, Any], foxy_config: Dict[str, Any]):
    if not stdout.isatty() or not stdin.isatty():
        print("WARNING: No interactive shell available, skipping first run wizard!", file=stderr)

        return
    print("New install detected, running first run wizard")
    use_og_pooling: bool = await confirm(message="Do you have OG (SOLO) plots you want to pool with?", default=foxy_config["enable_og_pooling"]).unsafe_ask_async()
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
            validate=lambda token: len(token) >= 16
        ).unsafe_ask_async()
        foxy_config["dr_plotter_client_token"] = dr_plotter_client_token

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

    if len(foxy_config["plot_nfts"]) == 0:
        should_sync_wallet: bool = await confirm(
            message="No PlotNFTs detected, do you want to sync the wallet to auto fill them?",
            default=True,
        ).unsafe_ask_async()
        if should_sync_wallet:
            plot_nft_updater = PlotNftUpdater(foxy_root=foxy_root, config=config, foxy_config=foxy_config)
            await plot_nft_updater.update_plot_nfts()
            plot_nft_count = len(foxy_config["plot_nfts"])
            if plot_nft_count == 0:
                print("No PlotNFTs found, skipping ..")
            else:
                print(f"Found {plot_nft_count} PlotNFT{'s' if plot_nft_count > 1 else ''}")

    if len(foxy_config["plot_nfts"]) > 0 and len(all_sks) > 0:
        should_print_login_links: bool = await confirm(
            message="Show the login links of your PlotNFTs?",
            default=True,
        ).unsafe_ask_async()
        if should_print_login_links:
            print("Login links for your PlotNFTs:")
            login_links = await generate_login_links(
                KeychainProxy(log=getLogger("first_run_wizard"), local_keychain=keychain),
                foxy_config["plot_nfts"],
            )
            for launcher_id, login_link in login_links:
                print()
                print(f"Launcher Id: {launcher_id}")
                print(f" Login Link: {login_link}")
            print()
