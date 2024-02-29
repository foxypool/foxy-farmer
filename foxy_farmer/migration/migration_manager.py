from dataclasses import dataclass
from pathlib import Path
from sys import stderr
from typing import Dict, Any, List

from yaml import safe_dump, safe_load

from foxy_farmer.config.foxy_config import FoxyConfig
from foxy_farmer.migration.migration import Migration, MigrationResult, aggregate_migration_results


@dataclass(frozen=True)
class MigrationManager:
    state_path: Path
    migrations: List[Migration]

    def run_migrations(self, foxy_farmer_config: FoxyConfig, chia_config: Dict[str, Any]) -> MigrationResult:
        executed_migrations = self._load_migrations()
        migrations_to_run = [m for m in self.migrations if executed_migrations.get(m.name) is not True]
        if len(migrations_to_run) == 0:
            return aggregate_migration_results([])
        migration_results: List[MigrationResult] = []
        for migration in migrations_to_run:
            print(f"Running migration {migration.name}")
            try:
                migration_results.append(migration.run(foxy_farmer_config=foxy_farmer_config, chia_config=chia_config))
            except Exception as e:
                print(f"Encountered an error while running migration {migration.name}: {e}", file=stderr)

                break
            executed_migrations[migration.name] = True
        self._save_migrations(executed_migrations)

        return aggregate_migration_results(migration_results)

    def _load_migrations(self) -> Dict[str, Any]:
        if self.state_path.exists() is False:
            self.state_path.parent.mkdir(parents=True, exist_ok=True)
            self._save_migrations({})
        with open(self.state_path, "r") as f:
            config = safe_load(f)
        return config

    def _save_migrations(self, migrations: Dict[str, Any]):
        with open(self.state_path, "w") as f:
            safe_dump(migrations, f)
