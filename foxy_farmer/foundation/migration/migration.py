from dataclasses import dataclass
from typing import Dict, Any, List


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
        return f"{self.date}-{type(self).__name__.replace('Migration', '')}"

    @property
    def date(self) -> str:
        ...

    def run(self, foxy_farmer_config: Dict[str, Any], chia_config: Dict[str, Any]) -> MigrationResult:
        ...
