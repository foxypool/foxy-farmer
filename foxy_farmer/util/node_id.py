from pathlib import Path
from typing import Dict, Any

from chia.server.server import calculate_node_id
from chia.types.blockchain_format.sized_bytes import bytes32


def calculate_harvester_node_id(root_path: Path, config: Dict[str, Any]) -> bytes32:
    relative_harvester_private_cert_path = config["harvester"]["ssl"]["private_crt"]

    return calculate_node_id(root_path / relative_harvester_private_cert_path)


def calculate_harvester_node_id_slug(root_path: Path, config: Dict[str, Any]) -> str:
    return calculate_harvester_node_id(root_path, config).hex()[:8]
