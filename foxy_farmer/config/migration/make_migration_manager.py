from foxy_farmer.config.migration.migration_manager import MigrationManager
from foxy_farmer.config.migration.migrations.copy_plot_nfts import CopyPlotNftsMigration
from foxy_farmer.config.migration.migrations.farmer_api_url import FarmerApiUrlMigration
from foxy_farmer.config.migration.migrations.remove_path_from_plot_nfts import RemovePathFromPlotNftsMigration


def make_migration_manager() -> MigrationManager:
    return MigrationManager(
        migrations=[
            CopyPlotNftsMigration(),
            FarmerApiUrlMigration(),
            RemovePathFromPlotNftsMigration(),
        ],
    )
