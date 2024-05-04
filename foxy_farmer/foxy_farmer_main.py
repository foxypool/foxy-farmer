import sys
from os import execv, spawnv, P_WAIT, _exit

import click
from multiprocessing import freeze_support
from pathlib import Path

from chia.cmds.keys import keys_cmd
from chia.cmds.passphrase import passphrase_cmd
from chia.cmds.plots import plots_cmd

from foxy_farmer import close_sentry
from foxy_farmer.cmds.init import init_cmd
from foxy_farmer.cmds.join_pool import join_pool_cmd
from foxy_farmer.cmds.farm_summary import summary_cmd
from foxy_farmer.cmds.authenticate import authenticate_cmd
from foxy_farmer.exceptions.already_running_exception import AlreadyRunningException
from foxy_farmer.util.root_path import get_root_path
from foxy_farmer.version import version


async def run_foxy_farmer(foxy_root: Path, config_path: Path) -> bool:
    from foxy_farmer.foxy_farmer_class import FoxyFarmer
    foxy_farmer = FoxyFarmer(foxy_root, config_path)
    await foxy_farmer.setup_process_global_state()
    try:
        return await foxy_farmer.run()
    except AlreadyRunningException:
        pass
    finally:
        close_sentry()

    return False


@click.group(
    help=f"\n======== Foxy-Farmer {version} ========\n",
    invoke_without_command=True,
    context_settings=dict(help_option_names=["-h", "--help"])
)
@click.option(
    '-c',
    '--config',
    default='foxy-farmer.yaml',
    help="Config file path",
    type=click.Path(),
    show_default=True
)
@click.option(
    '-r',
    '--root-path',
    default=get_root_path(),
    help="Chia root path",
    type=click.Path(),
    show_default=True
)
@click.version_option(version=version, message="Foxy-Farmer %(version)s")
@click.pass_context
def cli(ctx, config, root_path):
    ctx.ensure_object(dict)
    ctx.obj["root_path"] = Path(root_path).resolve()
    ctx.obj["config_path"] = Path(config).resolve()
    if ctx.invoked_subcommand is None:
        ctx.forward(run_cmd)


@cli.command("run", short_help="Run foxy-farmer, can be omitted")
@click.pass_context
def run_cmd(ctx, config=None, root_path=None):
    from chia.server.start_service import async_run
    should_restart_app = async_run(run_foxy_farmer(ctx.obj["root_path"], ctx.obj["config_path"]))

    if should_restart_app:
        if sys.platform == "win32":
            # On Windows we can not replace the process, spawn subprocess and wait for its termination instead
            _exit(spawnv(P_WAIT, sys.executable, sys.argv))
        else:
            execv(sys.executable, sys.argv)


cli.add_command(summary_cmd)
cli.add_command(join_pool_cmd)
cli.add_command(authenticate_cmd)
cli.add_command(keys_cmd)
cli.add_command(plots_cmd)
cli.add_command(passphrase_cmd)
cli.add_command(init_cmd)


def main() -> None:
    cli()


if __name__ == '__main__':
    freeze_support()
    main()
