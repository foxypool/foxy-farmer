from asyncio import run
from decimal import Decimal

import click
from pathlib import Path

from chia.cmds.cmds_util import cli_confirm
from chia.cmds.units import units
from chia.util.chia_logging import initialize_logging
from chia.util.config import load_config
from chia.util.ints import uint64

from foxy_farmer.error_reporting.error_reporting import close_sentry
from foxy_farmer.config.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_farmer.config.foxy_config_manager import FoxyConfigManager


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

    if fee >= 0.1:
        cli_confirm(f"You selected a fee of {fee} XCH, do you really want to continue? (y/n): ")

    fee_raw: uint64 = uint64(int(fee * units["chia"]))

    try:
        run(join_pool(foxy_root, config_path, fee=fee_raw))
    finally:
        close_sentry()


async def join_pool(foxy_root: Path, config_path: Path, fee: uint64):
    foxy_chia_config_manager = FoxyChiaConfigManager(foxy_root)
    await foxy_chia_config_manager.ensure_foxy_config(config_path)
    config_manager = FoxyConfigManager(config_path)
    foxy_config = config_manager.load_config()

    config = load_config(foxy_root, "config.yaml")

    initialize_logging(
        service_name="foxy_farmer",
        logging_config=config["logging"],
        root_path=foxy_root,
    )

    from foxy_farmer.pool.pool_joiner import PoolJoiner
    pool_joiner = PoolJoiner(foxy_root=foxy_root, config=config, foxy_config=foxy_config)
    did_update = await pool_joiner.join_pool(fee=fee)
    if did_update:
        config_manager.save_config(foxy_config)
