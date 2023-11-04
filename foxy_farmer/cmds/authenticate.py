from asyncio import run
from pathlib import Path
from typing import Dict, Any

import click
from chia.util.config import load_config

from foxy_farmer.error_reporting import close_sentry
from foxy_farmer.foxy_chia_config_manager import FoxyChiaConfigManager


@click.command("auth", short_help="Authenticate your Launcher Ids on the pool")
@click.pass_context
def authenticate_cmd(ctx) -> None:
    foxy_root: Path = ctx.obj["root_path"]
    config_path: Path = ctx.obj["config_path"]
    foxy_chia_config_manager = FoxyChiaConfigManager(foxy_root)
    foxy_chia_config_manager.ensure_foxy_config(config_path)

    config = load_config(foxy_root, "config.yaml")

    try:
        run(authenticate(foxy_root, config))
    finally:
        close_sentry()


async def authenticate(foxy_root: Path, config: Dict[str, Any]):
    from foxy_farmer.keychain.authenticator import Authenticator
    authenticator = Authenticator(foxy_root=foxy_root, config=config)
    await authenticator.authenticate()
