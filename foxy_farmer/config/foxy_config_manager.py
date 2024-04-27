from pathlib import Path
from sys import stderr, exit

from yaml import safe_dump, safe_load, MarkedYAMLError

from foxy_farmer.config.foxy_config import FoxyConfig


def _get_default_config() -> FoxyConfig:
    return {
        'backend': 'gigahorse',
        'enable_og_pooling': False,
        'plot_directories': [],
        'plot_refresh_interval_seconds': 900,
        'harvester_num_threads': 30,
        'farmer_reward_address': '',
        'pool_payout_address': '',
        'log_level': 'INFO',
        'listen_host': '127.0.0.1',
        'enable_harvester': True,
        'recompute_hosts': [],
    }


class FoxyConfigManager:
    _file_path: Path

    def __init__(self, file_path: Path):
        self._file_path = file_path

    def has_config(self) -> bool:
        return self._file_path.exists() and not self._is_config_file_empty()

    def load_config_or_get_default(self) -> FoxyConfig:
        if self.has_config():
            return self.load_config()

        return _get_default_config()

    def _is_config_file_empty(self) -> bool:
        with open(self._file_path, "r") as opened_config_file:
            return not bool(opened_config_file.read())

    def load_config(self) -> FoxyConfig:
        with open(self._file_path, "r") as opened_config_file:
            try:
                config = safe_load(opened_config_file)
            except MarkedYAMLError as e:
                context: str = "" if e.problem_mark is None else f" (line={e.problem_mark.line + 1}, column={e.problem_mark.column + 1})"
                print(f"Failed to parse {self._file_path}: {e.problem}{context}.", file=stderr)
                print(f"Please make sure your config is properly formatted.", file=stderr)

                exit(1)
        return config

    def save_config(self, config: FoxyConfig):
        with open(self._file_path, "w") as f:
            safe_dump(config, f)
