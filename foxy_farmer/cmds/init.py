from pathlib import Path

import click

from foxy_farmer.foxy_chia_config_manager import FoxyChiaConfigManager


@click.command("init", short_help="Ensure the configurations are available")
@click.pass_context
def init_cmd(ctx) -> None:
    foxy_root: Path = ctx.obj["root_path"]
    config_path: Path = ctx.obj["config_path"]

    foxy_chia_config_manager = FoxyChiaConfigManager(foxy_root)
    foxy_chia_config_manager.ensure_foxy_config(config_path)

    print("Init done")