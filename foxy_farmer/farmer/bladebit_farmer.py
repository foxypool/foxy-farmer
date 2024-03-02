from pathlib import Path

from chia.util.config import load_config

from foxy_farmer.config.foxy_config import FoxyConfig
from foxy_farmer.environment.embedded_chia_environment import EmbeddedChiaEnvironment
from foxy_farmer.farmer.chia_farmer import ChiaFarmer


class BladebitFarmer(ChiaFarmer):
    def __init__(self, root_path: Path, farmer_config: FoxyConfig):
        self._farmer_config = farmer_config
        config = load_config(root_path, "config.yaml")
        self._environment = EmbeddedChiaEnvironment(
            root_path=root_path,
            config=config,
            allow_connecting_to_existing_daemon=False,
        )
