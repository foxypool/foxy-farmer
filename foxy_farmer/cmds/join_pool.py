from asyncio import run

import click
from pathlib import Path

from chia.util.chia_logging import initialize_logging
from chia.util.config import load_config

from foxy_farmer.error_reporting import close_sentry
from foxy_farmer.foxy_chia_config_manager import FoxyChiaConfigManager


@click.command("join-pool", short_help="Join your PlotNFTs to the pool")
@click.pass_context
def join_pool_cmd(ctx) -> None:
    foxy_root: Path = ctx.obj["root_path"]
    config_path: Path = ctx.obj["config_path"]
    foxy_chia_config_manager = FoxyChiaConfigManager(foxy_root)
    foxy_chia_config_manager.ensure_foxy_config(config_path)

    try:
        run(join_pool(foxy_root, config_path))
    finally:
        close_sentry()


async def join_pool(foxy_root: Path, config_path: Path):
    config = load_config(foxy_root, "config.yaml")

    initialize_logging(
        service_name="foxy_farmer",
        logging_config=config["logging"],
        root_path=foxy_root,
    )

    from foxy_farmer.pool.pool_joiner import PoolJoiner
    pool_joiner = PoolJoiner(foxy_root=foxy_root, config=config, config_path=config_path)
    await pool_joiner.join_pool()
