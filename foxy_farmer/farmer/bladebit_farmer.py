from pathlib import Path
from typing import Any, Dict

from chia.util.config import load_config

from foxy_farmer.environment import EmbeddedChiaEnvironment
from foxy_farmer.farmer.farmer import Farmer


class BladebitFarmer(Farmer):
    def __init__(self, root_path: Path, farmer_config: Dict[str, Any]):
        self._farmer_config = farmer_config
        config = load_config(root_path, "config.yaml")
        self._environment = EmbeddedChiaEnvironment(
            root_path=root_path,
            config=config,
            allow_connecting_to_existing_daemon=False,
        )
