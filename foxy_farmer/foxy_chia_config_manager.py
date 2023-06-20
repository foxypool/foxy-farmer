from pathlib import Path
from shutil import copyfile
from typing import Dict

from chia.cmds.init_funcs import chia_init
from chia.util.bech32m import decode_puzzle_hash
from chia.util.config import load_config, save_config
from chia.util.default_root import DEFAULT_ROOT_PATH

from foxy_farmer.foxy_config_manager import FoxyConfigManager
from foxy_farmer.foxy_farming_gateway import foxy_farming_gateway_address, foxy_farming_gateway_port


class FoxyChiaConfigManager:
    _root_path: Path

    def __init__(self, root_path: Path):
        self._root_path = root_path

    def ensure_foxy_config(self, config_path: Path):
        foxy_chia_config_file_path = self._root_path / "config" / "config.yaml"
        is_first_install = foxy_chia_config_file_path.exists() is False
        if is_first_install:
            chia_init(self._root_path)

        chia_root = DEFAULT_ROOT_PATH
        chia_config_file_path = chia_root / "config" / "config.yaml"
        if is_first_install is True and chia_config_file_path.exists():
            copyfile(chia_config_file_path, self._root_path / "config" / "config.yaml")

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

        # Init the foxy_farmer config from the chia foxy config
        if has_foxy_config is False:
            foxy_config["plot_directories"] = config["harvester"]["plot_directories"]
            foxy_config["harvester_num_threads"] = config["harvester"]["num_threads"]
            foxy_config["farmer_reward_address"] = config["farmer"]["xch_target_address"]
            foxy_config["pool_payout_address"] = config["farmer"]["xch_target_address"]
            foxy_config_manager.save_config(foxy_config)

        config_was_updated = self.ensure_different_ports(config, config_was_updated)
        config_was_updated = self.ensure_foxy_gateway(config, config_was_updated)
        config_was_updated = self.update_foxy_chia_config_from_foxy_config(
            chia_foxy_config=config,
            foxy_config=foxy_config,
            config_was_updated=config_was_updated
        )

        if config_was_updated:
            save_config(self._root_path, "config.yaml", config)

    def update_foxy_chia_config_from_foxy_config(
            self,
            chia_foxy_config: Dict,
            foxy_config: Dict,
            config_was_updated: bool = False
    ):
        if chia_foxy_config["logging"]["log_level"] != foxy_config["log_level"] or chia_foxy_config["logging"]["log_stdout"] is not False:
            chia_foxy_config["logging"]["log_level"] = foxy_config["log_level"]
            chia_foxy_config["logging"]["log_stdout"] = False
            config_was_updated = True
        if chia_foxy_config["self_hostname"] != foxy_config["listen_host"]:
            chia_foxy_config["self_hostname"] = foxy_config["listen_host"]
            config_was_updated = True
        if chia_foxy_config["harvester"]["num_threads"] != foxy_config["harvester_num_threads"]:
            chia_foxy_config["harvester"]["num_threads"] = foxy_config["harvester_num_threads"]
            config_was_updated = True
        if chia_foxy_config["harvester"]["plot_directories"] != foxy_config["plot_directories"]:
            chia_foxy_config["harvester"]["plot_directories"] = foxy_config["plot_directories"]
            config_was_updated = True
        if chia_foxy_config["harvester"].get("plots_refresh_parameter") is not None and chia_foxy_config["harvester"]["plots_refresh_parameter"]["interval_seconds"] != foxy_config["plot_refresh_interval_seconds"]:
            chia_foxy_config["harvester"]["plots_refresh_parameter"]["interval_seconds"] = foxy_config["plot_refresh_interval_seconds"]
            config_was_updated = True

        if chia_foxy_config["farmer"]["xch_target_address"] != foxy_config["farmer_reward_address"]:
            chia_foxy_config["farmer"]["xch_target_address"] = foxy_config["farmer_reward_address"]
            config_was_updated = True

        # Ensure all nft pools use the same payout address
        pool_payout_address_ph = decode_puzzle_hash(foxy_config["pool_payout_address"]).hex()
        if chia_foxy_config["pool"].get("pool_list") is not None:
            for pool in chia_foxy_config["pool"]["pool_list"]:
                if pool["payout_instructions"] != pool_payout_address_ph:
                    pool["payout_instructions"] = pool_payout_address_ph
                    config_was_updated = True

        # Update og payout address if og pooling is enabled
        if foxy_config["enable_og_pooling"] is True and chia_foxy_config["farmer"].get("pool_payout_address") != foxy_config["pool_payout_address"]:
            chia_foxy_config["farmer"]["pool_payout_address"] = foxy_config["pool_payout_address"]
            config_was_updated = True

        # Ensure we explicitly disable og pooling as the og client defaults to og pooling
        if chia_foxy_config["farmer"].get("disable_og_pooling") is None or chia_foxy_config["farmer"]["disable_og_pooling"] == foxy_config["enable_og_pooling"]:
            chia_foxy_config["farmer"]["disable_og_pooling"] = not foxy_config["enable_og_pooling"]
            config_was_updated = True

        # Ensure the og reward address is the farmer reward address if not og pooling
        if foxy_config["enable_og_pooling"] is False and chia_foxy_config["pool"]["xch_target_address"] != foxy_config["farmer_reward_address"]:
            chia_foxy_config["pool"]["xch_target_address"] = foxy_config["farmer_reward_address"]
            config_was_updated = True

        return config_was_updated

    def ensure_foxy_gateway(self, config: Dict, config_was_updated: bool = False):
        if config["farmer"]["full_node_peer"]["host"] != foxy_farming_gateway_address or config["farmer"]["full_node_peer"]["port"] != foxy_farming_gateway_port:
            config["farmer"]["full_node_peer"]["host"] = foxy_farming_gateway_address
            config["farmer"]["full_node_peer"]["port"] = foxy_farming_gateway_port
            config_was_updated = True

        return config_was_updated

    def ensure_different_ports(self, config: Dict, config_was_updated: bool = False):
        if config["daemon_port"] != 55469:
            config["daemon_port"] = 55469
            config_was_updated = True
        if config["farmer"]["harvester_peer"]["port"] != 18448:
            config["farmer"]["harvester_peer"]["port"] = 18448
            config_was_updated = True
        if config["farmer"]["port"] != 18447:
            config["farmer"]["port"] = 18447
            config_was_updated = True
        if config["farmer"]["rpc_port"] != 18559:
            config["farmer"]["rpc_port"] = 18559
            config_was_updated = True
        if config["harvester"]["farmer_peer"]["port"] != 18447:
            config["harvester"]["farmer_peer"]["port"] = 18447
            config_was_updated = True
        if config["harvester"]["port"] != 18448:
            config["harvester"]["port"] = 18448
            config_was_updated = True
        if config["harvester"]["rpc_port"] != 18560:
            config["harvester"]["rpc_port"] = 18560
            config_was_updated = True

        return config_was_updated
