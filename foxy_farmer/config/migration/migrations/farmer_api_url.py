from typing import Dict, Any

from foxy_farmer.config.foxy_config import FoxyConfig
from foxy_farmer.config.migration.migration import Migration, MigrationResult


class FarmerApiUrlMigration(Migration):
    @property
    def version(self) -> int:
        return 2

    def run(self, foxy_farmer_config: FoxyConfig, chia_config: Dict[str, Any]) -> MigrationResult:
        if foxy_farmer_config.get("plot_nfts") is None:
            return MigrationResult()

        did_update_foxy_farmer_config = False
        for plot_nft in foxy_farmer_config["plot_nfts"]:
            if "farmer.chia.foxypool.io" not in plot_nft["pool_url"]:
                continue
            plot_nft["pool_url"] = plot_nft["pool_url"].replace("farmer.chia.foxypool.io", "farmer-chia.foxypool.io")
            did_update_foxy_farmer_config = True

        return MigrationResult(did_update_foxy_farmer_config=did_update_foxy_farmer_config)
