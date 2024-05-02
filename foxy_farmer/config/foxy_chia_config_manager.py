from os import environ
from pathlib import Path
from shutil import copyfile
from typing import Dict, Any, List, Callable, Union
from sys import exit

from chia.cmds.init_funcs import chia_init, check_keys
from chia.cmds.keys_funcs import add_private_key_seed
from chia.util.config import load_config, save_config
from chia.util.default_root import DEFAULT_ROOT_PATH, DEFAULT_KEYS_ROOT_PATH
from chia.util.keychain import Keychain

from foxy_farmer.binary_manager.dr_plotter_binary_manager import dr_plotter_binary_release
from foxy_farmer.config.foxy_config import FoxyConfig, PlotNft
from foxy_farmer.ff_logging.configure_logging import disabled_logging
from foxy_farmer.first_run.first_run_wizard import run_first_run_wizard
from foxy_farmer.config.backend import Backend
from foxy_farmer.config.config_patcher import ConfigPatcher
from foxy_farmer.config.foxy_config_manager import FoxyConfigManager
from foxy_farmer.config.foxy_farming_gateway import eu1_foxy_farming_gateway_address, foxy_farming_gateway_port, \
    eu3_foxy_farming_gateway_address, eu1_foxy_gigahorse_farming_gateway_address, foxy_gigahorse_farming_gateway_port, \
    eu3_foxy_gigahorse_farming_gateway_address
from foxy_farmer.migration.make_migration_manager import make_migration_manager
from foxy_farmer.version import version


class FoxyChiaConfigManager:
    _root_path: Path

    def __init__(self, root_path: Path):
        self._root_path = root_path

    async def ensure_foxy_config(self, config_path: Path):
        foxy_chia_config_file_path = self._root_path / "config" / "config.yaml"
        is_first_install = foxy_chia_config_file_path.exists() is False
        if is_first_install:
            chia_init(self._root_path, fix_ssl_permissions=True)

        chia_root = DEFAULT_ROOT_PATH
        chia_config_file_path = chia_root / "config" / "config.yaml"
        if is_first_install is True and chia_config_file_path.exists():
            copyfile(chia_config_file_path, self._root_path / "config" / "config.yaml")

        if (not DEFAULT_KEYS_ROOT_PATH.exists() or not has_keys()) and environ.get("CHIA_MNEMONIC") is not None:
            add_private_key_seed(environ["CHIA_MNEMONIC"].strip(), None)
            check_keys(self._root_path)

        config = load_config(self._root_path, "config.yaml")

        # Ensure we always have the 'xch_target_address' key set
        config_was_updated = False
        if "xch_target_address" not in config["farmer"]:
            config["farmer"]["xch_target_address"] = ""
            config_was_updated = True
        if "xch_target_address" not in config["pool"]:
            config["pool"]["xch_target_address"] = ""
            config_was_updated = True

        foxy_config_manager = FoxyConfigManager(config_path)
        has_foxy_config = foxy_config_manager.has_config()
        foxy_config = foxy_config_manager.load_config_or_get_default()

        foxy_config_was_updated = False
        # Init the foxy_farmer config from the chia foxy config
        if has_foxy_config is False:
            foxy_config["plot_directories"] = config["harvester"]["plot_directories"]
            foxy_config["harvester_num_threads"] = config["harvester"]["num_threads"]
            foxy_config["farmer_reward_address"] = config["farmer"]["xch_target_address"]
            foxy_config["pool_payout_address"] = config["farmer"]["xch_target_address"]
            foxy_config["plot_nfts"] = config["pool"].get("pool_list", [])
            foxy_config_was_updated = True

        if foxy_config["farmer_reward_address"] == "" and config["farmer"]["xch_target_address"] != "":
            foxy_config["farmer_reward_address"] = config["farmer"]["xch_target_address"]
            foxy_config_was_updated = True
        if foxy_config["pool_payout_address"] == "" and config["farmer"]["xch_target_address"] != "":
            foxy_config["pool_payout_address"] = config["farmer"]["xch_target_address"]
            foxy_config_was_updated = True

        if not has_foxy_config:
            with disabled_logging():
                await run_first_run_wizard(foxy_root=self._root_path, config=config, foxy_config=foxy_config)
            foxy_config_manager.save_config(foxy_config)
            foxy_config_was_updated = False

        if foxy_config.get("farmer_reward_address", "") == "" or foxy_config.get("pool_payout_address", "") == "":
            if foxy_config_was_updated:
                foxy_config_manager.save_config(foxy_config)
            print(f"You are missing a 'farmer_reward_address' and/or 'pool_payout_address' in {config_path}, please update the config and run again.")
            exit(1)

        migration_manager = make_migration_manager()
        result = migration_manager.run_migrations(foxy_farmer_config=foxy_config, chia_config=config)

        config_was_updated = config_was_updated or result.did_update_chia_config
        foxy_config_was_updated = foxy_config_was_updated or result.did_update_foxy_farmer_config

        if foxy_config_was_updated:
            foxy_config_manager.save_config(foxy_config)

        if config_was_updated:
            save_config(self._root_path, "config.yaml", config)

        config_patcher = ConfigPatcher(foxy_farmer_config=foxy_config, chia_config=config)
        self.patch_configs(
            config_patcher=config_patcher,
            chia_config=config,
            foxy_farmer_config=foxy_config,
        )

        config_patcher_result = config_patcher.get_result()
        if config_patcher_result.foxy_farmer_config_was_updated:
            foxy_config_manager.save_config(foxy_config)

        if config_patcher_result.chia_config_was_updated:
            save_config(self._root_path, "config.yaml", config)

    def patch_configs(
        self,
        config_patcher: ConfigPatcher,
        chia_config: Dict[str, Any],
        foxy_farmer_config: FoxyConfig,
    ):
        backend: Union[str, Backend] = foxy_farmer_config.get("backend", Backend.BladeBit)
        require_syslog = backend != Backend.BladeBit
        full_node_peers: List[Dict[str, Any]] = [{
            "host": eu1_foxy_farming_gateway_address,
            "port": foxy_farming_gateway_port,
        }, {
            "host": eu3_foxy_farming_gateway_address,
            "port": foxy_farming_gateway_port,
        }]
        if backend == Backend.Gigahorse:
            full_node_peers = [{
                "host": eu1_foxy_gigahorse_farming_gateway_address,
                "port": foxy_gigahorse_farming_gateway_port,
            }, {
                "host": eu3_foxy_gigahorse_farming_gateway_address,
                "port": foxy_gigahorse_farming_gateway_port,
            }]

        (config_patcher
            # Ensure different ports
            .patch_value("daemon_port", foxy_farmer_config.get("chia_daemon_port", 55469))
            .patch_value("farmer.port", foxy_farmer_config.get("chia_farmer_port", 18447))
            .patch_value("farmer.rpc_port", foxy_farmer_config.get("chia_farmer_rpc_port", 18559))
            .remove_config_key("harvester.farmer_peer")
            .patch_value("harvester.farmer_peers", [{
                "host": foxy_farmer_config.get("listen_host"),
                "port": foxy_farmer_config.get("chia_farmer_port", 18447),
            }])
            .patch_value("harvester.rpc_port", foxy_farmer_config.get("chia_harvester_rpc_port", 18560))
            .patch_value("wallet.rpc_port", foxy_farmer_config.get("chia_wallet_rpc_port", 19256))
            # Ensure the wallet does not try to connect to localhost
            .remove_config_key("wallet.full_node_peer")
            .remove_config_key("wallet.full_node_peers")
            # Ensure we connect to the farming gateway
            .remove_config_key("farmer.full_node_peer")
            .patch_value("farmer.full_node_peers", full_node_peers)
            # Sync logging
            .patch("log_level", "logging.log_level")
            .patch_value("logging.log_stdout", False)
            .patch_value("logging.log_syslog", require_syslog)
            .patch_value("logging.log_syslog_host", "127.0.0.1")
            .patch_value("logging.log_syslog_port", foxy_farmer_config.get("syslog_port", 11514))
            .patch("listen_host", "self_hostname")
            # Sync harvester
            .patch("harvester_num_threads", "harvester.num_threads")
            .patch("plot_directories", "harvester.plot_directories")
            .patch("recursive_plot_scan", "harvester.recursive_plot_scan")
            .patch("parallel_decompressor_count", "harvester.parallel_decompressor_count")
            .patch("decompressor_thread_count", "harvester.decompressor_thread_count")
            .patch("disable_cpu_affinity", "harvester.disable_cpu_affinity")
            .patch("max_compression_level_allowed", "harvester.max_compression_level_allowed")
            .patch("use_gpu_harvesting", "harvester.use_gpu_harvesting")
            .patch("gpu_index", "harvester.gpu_index")
            .patch("enforce_gpu_index", "harvester.enforce_gpu_index")
            .patch("decompressor_timeout", "harvester.decompressor_timeout")
            .patch("plot_refresh_interval_seconds", "harvester.plots_refresh_parameter.interval_seconds")
            .patch("plot_refresh_batch_size", "harvester.plots_refresh_parameter.batch_size")
            .patch("plot_refresh_batch_sleep_ms", "harvester.plots_refresh_parameter.batch_sleep_milliseconds")
            # Sync reward and payout addresses
            .patch("farmer_reward_address", "farmer.xch_target_address")
            .sync_pool_payout_address()
            # Ensure we explicitly disable og pooling as the og client defaults to og pooling
            .patch_value("farmer.disable_og_pooling", not foxy_farmer_config.get("enable_og_pooling", False))
            # Ensure the wallet syncs with unknown peers
            .patch_value("wallet.connect_to_unknown_peers", True)
            # Ensure we do not filter out PlotNFT creation and state changes
            .patch_value("wallet.xch_spam_amount", 0)
            .patch_value("wallet.use_delta_sync", True)
         )

        if backend == Backend.Gigahorse:
            config_patcher.patch_pool_list_closure(make_ensure_client_path_in_pool_url(f"ff-{version}"))
        elif backend == Backend.DrPlotter:
            config_patcher.patch_pool_list_closure(make_ensure_client_path_in_pool_url(f"dr-{dr_plotter_binary_release}"))

        if foxy_farmer_config.get("enable_og_pooling", False) is True:
            # Update og payout address
            config_patcher.patch("pool_payout_address", "farmer.pool_payout_address")
            # Ensure the pool reward address is set to any valid address, the og client will auto adjust to the correct
            # address on launch
            if chia_config["pool"]["xch_target_address"] == "":
                config_patcher.patch("farmer_reward_address", "pool.xch_target_address")
        else:
            # Ensure the og reward address is the farmer reward address
            config_patcher.patch("farmer_reward_address", "pool.xch_target_address")


def make_ensure_client_path_in_pool_url(client_path: str) -> Callable[[PlotNft], bool]:
    def ensure_client_path_in_pool_url(pool: PlotNft) -> bool:
        pool_url = pool["pool_url"]
        if "foxypool.io" not in pool_url:
            return False
        url_parts = pool_url.split("/")

        if len(url_parts) == 3:
            url_parts.append(client_path)
        elif url_parts[-1] != client_path:
            url_parts[-1] = client_path
        new_pool_url = "/".join(url_parts)
        if pool_url != new_pool_url:
            pool["pool_url"] = new_pool_url

            return True

        return False

    return ensure_client_path_in_pool_url


def has_keys() -> bool:
    keychain = Keychain()
    all_sks = keychain.get_all_private_keys()

    return len(all_sks) > 0
