from os.path import expanduser
from pathlib import Path

from foxy_farmer.migration.migration_manager import MigrationManager
from foxy_farmer.migration.migrations.copy_plot_nfts import CopyPlotNftsMigration
from foxy_farmer.migration.migrations.farmer_api_url import FarmerApiUrlMigration


def make_migration_manager() -> MigrationManager:
    return MigrationManager(
        state_path=Path(expanduser("~/.foxy-farmer/migrations.yaml")).resolve(),
        migrations=[
            CopyPlotNftsMigration(),
            FarmerApiUrlMigration(),
        ],
    )
