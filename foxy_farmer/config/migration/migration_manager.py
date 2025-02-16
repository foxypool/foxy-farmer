from dataclasses import dataclass
from sys import stderr
from typing import Dict, Any, List

from foxy_farmer.config.foxy_config import FoxyConfig
from foxy_farmer.config.migration.migration import Migration, MigrationResult, aggregate_migration_results


@dataclass(frozen=True)
class MigrationManager:
    migrations: List[Migration]

    def run_migrations(self, foxy_farmer_config: FoxyConfig, chia_config: Dict[str, Any]) -> MigrationResult:
        migration_version = foxy_farmer_config.get("migration_version") or 0
        migrations_to_run = [m for m in self.migrations if m.version > migration_version]
        if len(migrations_to_run) == 0:
            return aggregate_migration_results([])
        migrations_to_run.sort(key=lambda m: m.version)
        migration_results: List[MigrationResult] = []
        for migration in migrations_to_run:
            print(f"Running migration {migration.name}")
            try:
                migration_results.append(migration.run(foxy_farmer_config=foxy_farmer_config, chia_config=chia_config))
            except Exception as e:
                print(f"Encountered an error while running migration {migration.name}: {e}", file=stderr)

                break
            foxy_farmer_config["migration_version"] = migration.version
            migration_results.append(MigrationResult(did_update_foxy_farmer_config=True, did_update_chia_config=False))

        return aggregate_migration_results(migration_results)
