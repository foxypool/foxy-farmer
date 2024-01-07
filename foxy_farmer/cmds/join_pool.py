from asyncio import run
from decimal import Decimal

import click
from pathlib import Path

from chia.cmds.cmds_util import cli_confirm
from chia.cmds.units import units
from chia.util.chia_logging import initialize_logging
from chia.util.config import load_config
from chia.util.ints import uint64

from foxy_farmer.error_reporting import close_sentry
from foxy_farmer.foxy_chia_config_manager import FoxyChiaConfigManager


@click.command("join-pool", short_help="Join your PlotNFTs to the pool")
@click.option(
    '-f',
    '--fee',
    default=Decimal(0),
    help="Fee to use for each pool join, in XCH",
    type=Decimal,
    show_default=True
)
@click.pass_context
def join_pool_cmd(ctx, fee: Decimal) -> None:
    foxy_root: Path = ctx.obj["root_path"]
    config_path: Path = ctx.obj["config_path"]
    foxy_chia_config_manager = FoxyChiaConfigManager(foxy_root)
    foxy_chia_config_manager.ensure_foxy_config(config_path)

    if fee >= 0.1:
        cli_confirm(f"You selected a fee of {fee} XCH, do you really want to continue? (y/n): ")

    fee_raw: uint64 = uint64(int(fee * units["chia"]))

    try:
        run(join_pool(foxy_root, config_path, fee=fee_raw))
    finally:
        close_sentry()


async def join_pool(foxy_root: Path, config_path: Path, fee: uint64):
    config = load_config(foxy_root, "config.yaml")

    initialize_logging(
        service_name="foxy_farmer",
        logging_config=config["logging"],
        root_path=foxy_root,
    )

    from foxy_farmer.pool.pool_joiner import PoolJoiner
    pool_joiner = PoolJoiner(foxy_root=foxy_root, config=config, config_path=config_path)
    await pool_joiner.join_pool(fee=fee)
