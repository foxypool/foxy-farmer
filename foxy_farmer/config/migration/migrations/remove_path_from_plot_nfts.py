from typing import Dict, Any

from foxy_farmer.config.foxy_config import FoxyConfig
from foxy_farmer.config.migration.migration import Migration, MigrationResult


class RemovePathFromPlotNftsMigration(Migration):
    @property
    def version(self) -> int:
        return 3

    def run(self, foxy_farmer_config: FoxyConfig, chia_config: Dict[str, Any]) -> MigrationResult:
        if foxy_farmer_config.get("plot_nfts") is None:
            return MigrationResult()

        did_update = False
        for plot_nft in foxy_farmer_config["plot_nfts"]:
            pool_url = plot_nft["pool_url"]
            if "foxypool.io" not in pool_url:
                continue

            url_parts = pool_url.split("/")
            if len(url_parts) == 3:
                continue

            plot_nft["pool_url"] = "/".join(url_parts[:-1])
            did_update = True

        return MigrationResult(did_update_foxy_farmer_config=did_update)
