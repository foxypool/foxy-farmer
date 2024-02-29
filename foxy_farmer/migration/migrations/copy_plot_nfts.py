from typing import Dict, Any

from foxy_farmer.migration.migration import Migration, MigrationResult


class CopyPlotNftsMigration(Migration):
    @property
    def date(self) -> str:
        return "2024-01-25"

    def run(self, foxy_farmer_config: Dict[str, Any], chia_config: Dict[str, Any]) -> MigrationResult:
        if foxy_farmer_config.get("plot_nfts") is not None:
            return MigrationResult()
        foxy_farmer_config["plot_nfts"] = chia_config["pool"].get('pool_list', [])

        return MigrationResult(did_update_foxy_farmer_config=True)
