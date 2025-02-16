from dataclasses import dataclass
from typing import Dict, Any, List

from foxy_farmer.config.foxy_config import FoxyConfig


@dataclass
class MigrationResult:
    did_update_foxy_farmer_config: bool = False
    did_update_chia_config: bool = False


def aggregate_migration_results(results: List[MigrationResult]) -> MigrationResult:
    did_update_foxy_farmer_config = False
    did_update_chia_config = False
    for result in results:
        did_update_foxy_farmer_config = did_update_foxy_farmer_config or result.did_update_foxy_farmer_config
        did_update_chia_config = did_update_chia_config or result.did_update_chia_config

    return MigrationResult(did_update_foxy_farmer_config, did_update_chia_config)


class Migration:
    @property
    def name(self):
        return f"v{self.version} - {type(self).__name__.replace('Migration', '')}"

    @property
    def version(self) -> int:
        ...

    def run(self, foxy_farmer_config: FoxyConfig, chia_config: Dict[str, Any]) -> MigrationResult:
        ...
