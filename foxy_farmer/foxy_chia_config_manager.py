from os import environ
from pathlib import Path
from shutil import copyfile
from typing import Dict, Any

from chia.cmds.init_funcs import chia_init, check_keys
from chia.cmds.keys_funcs import add_private_key_seed
from chia.util.config import load_config, save_config
from chia.util.default_root import DEFAULT_ROOT_PATH, DEFAULT_KEYS_ROOT_PATH

from foxy_farmer.foundation.config.config_patcher import ConfigPatcher
from foxy_farmer.foxy_config_manager import FoxyConfigManager


class FoxyChiaConfigManager:
    _root_path: Path

    def __init__(self, root_path: Path):
        self._root_path = root_path

    def ensure_foxy_config(self, config_path: Path):
        foxy_chia_config_file_path = self._root_path / "config" / "config.yaml"
        is_first_install = foxy_chia_config_file_path.exists() is False
        if is_first_install:
            chia_init(self._root_path, fix_ssl_permissions=True)

        chia_root = DEFAULT_ROOT_PATH
        chia_config_file_path = chia_root / "config" / "config.yaml"
        if is_first_install is True and chia_config_file_path.exists():
            copyfile(chia_config_file_path, self._root_path / "config" / "config.yaml")

        if not DEFAULT_KEYS_ROOT_PATH.exists() and environ.get("CHIA_MNEMONIC") is not None:
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
        foxy_config = foxy_config_manager.load_config()

        foxy_config_was_updated = False
        # Init the foxy_farmer config from the chia foxy config
        if has_foxy_config is False:
            foxy_config["plot_directories"] = config["harvester"]["plot_directories"]
            foxy_config["harvester_num_threads"] = config["harvester"]["num_threads"]
            foxy_config["farmer_reward_address"] = config["farmer"]["xch_target_address"]
            foxy_config["pool_payout_address"] = config["farmer"]["xch_target_address"]
            foxy_config_was_updated = True

        if foxy_config["farmer_reward_address"] == "" and config["farmer"]["xch_target_address"] != "":
            foxy_config["farmer_reward_address"] = config["farmer"]["xch_target_address"]
            foxy_config_was_updated = True
        if foxy_config["pool_payout_address"] == "" and config["farmer"]["xch_target_address"] != "":
            foxy_config["pool_payout_address"] = config["farmer"]["xch_target_address"]
            foxy_config_was_updated = True

        if foxy_config.get("farmer_reward_address", "") == "" or foxy_config.get("pool_payout_address", "") == "":
            if foxy_config_was_updated:
                foxy_config_manager.save_config(foxy_config)
            print(f"You are missing a 'farmer_reward_address' and/or 'pool_payout_address' in {config_path}, please update the config and run again.")
            exit(1)

        config_patcher = ConfigPatcher(foxy_farmer_config=foxy_config, chia_config=config)
        self.patch_configs(
            config_patcher=config_patcher,
            chia_config=config,
            foxy_farmer_config=foxy_config,
        )

        config_patcher_result = config_patcher.get_result()
        config_was_updated = config_was_updated or config_patcher_result.chia_config_was_updated
        foxy_config_was_updated = foxy_config_was_updated or config_patcher_result.foxy_farmer_config_was_updated

        if foxy_config_was_updated:
            foxy_config_manager.save_config(foxy_config)

        if config_was_updated:
            save_config(self._root_path, "config.yaml", config)

    def patch_configs(
        self,
        config_patcher: ConfigPatcher,
        chia_config: Dict[str, Any],
        foxy_farmer_config: Dict[str, Any],
    ):
        (config_patcher
            # Ensure different ports
            .patch_value("daemon_port", foxy_farmer_config.get("chia_daemon_port", 55469))
            .patch_value("farmer.port", foxy_farmer_config.get("chia_farmer_port", 18447))
            .patch_value("farmer.rpc_port", foxy_farmer_config.get("chia_farmer_rpc_port", 18559))
            # Deprecated: harvester port can be dropped with the next chia release
            .patch_value("harvester.port", foxy_farmer_config.get("chia_harvester_port", 18448))
            .patch_value("harvester.rpc_port", foxy_farmer_config.get("chia_harvester_rpc_port", 18560))
            .patch_value("wallet.rpc_port", foxy_farmer_config.get("chia_wallet_rpc_port", 19256))
            # Ensure the wallet does not try to connect to localhost
            .remove_config_key("wallet.full_node_peer")
            .remove_config_key("wallet.full_node_peers")
            # Sync logging
            .patch("log_level", "logging.log_level")
            .patch_value("logging.log_stdout", False)
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
            .patch_value("farmer.disable_og_pooling", not foxy_farmer_config["enable_og_pooling"])
            # Ensure the wallet syncs with unknown peers
            .patch_value("wallet.connect_to_unknown_peers", True)
         )

        if foxy_farmer_config["enable_og_pooling"] is True:
            # Update og payout address
            config_patcher.patch("pool_payout_address", "farmer.pool_payout_address")
            # Ensure the pool reward address is set to any valid address, the og client will auto adjust to the correct
            # address on launch
            if chia_config["pool"]["xch_target_address"] == "":
                config_patcher.patch("farmer_reward_address", "pool.xch_target_address")
        else:
            # Ensure the og reward address is the farmer reward address
            config_patcher.patch("farmer_reward_address", "pool.xch_target_address")

        # Deprecated: Update to set list of peers with next chia release. Drop adding peers in service factory.
        config_patcher.remove_config_key("farmer.full_node_peer")
