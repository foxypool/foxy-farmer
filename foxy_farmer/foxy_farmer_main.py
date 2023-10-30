from multiprocessing import freeze_support

from foxy_farmer.monkey_patch_chia_version import monkey_patch_chia_version

monkey_patch_chia_version()

import asyncio
import logging
import os
import signal
from pathlib import Path
from types import FrameType
from typing import Optional

import click
import pkg_resources

from chia.cmds.keys import keys_cmd
from chia.cmds.passphrase import passphrase_cmd
from chia.cmds.plots import plots_cmd
from chia.farmer.farmer_api import FarmerAPI
from chia.harvester.harvester_api import HarvesterAPI
from chia.farmer.farmer import Farmer
from chia.harvester.harvester import Harvester
from chia.server.start_service import async_run, Service
from chia.util.config import load_config
from chia.util.misc import SignalHandlers

from foxy_farmer.chia_launcher import ChiaLauncher
from foxy_farmer.cmds.join_pool import join_pool_cmd
from foxy_farmer.cmds.farm_summary import summary_cmd
from foxy_farmer.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_farmer.foxy_config_manager import FoxyConfigManager
from foxy_farmer.foxy_farmer_logging import initialize_logging_with_stdout
from foxy_farmer.service_factory import ServiceFactory
from foxy_farmer.cmds.authenticate import authenticate_cmd

log = logging.getLogger("foxy_farmer")
version = pkg_resources.require("foxy-farmer")[0].version


class FoxyFarmer:
    _foxy_root: Path
    _config_path: Path
    _chia_launcher: Optional[ChiaLauncher]
    _farmer_service: Service[Farmer, FarmerAPI]
    _harvester_service: Optional[Service[Harvester, HarvesterAPI]] = None

    def __init__(self, foxy_root: Path, config_path: Path):
        self._foxy_root = foxy_root
        self._config_path = config_path

    async def start(self):
        foxy_chia_config_manager = FoxyChiaConfigManager(self._foxy_root)
        foxy_chia_config_manager.ensure_foxy_config(self._config_path)

        config = load_config(self._foxy_root, "config.yaml")
        initialize_logging_with_stdout(
            logging_config=config["logging"],
            root_path=self._foxy_root,
        )

        log.info(f"Foxy-Farmer {version} using config in {self._config_path}")

        service_factory = ServiceFactory(self._foxy_root, config)
        self._farmer_service = service_factory.make_farmer()

        foxy_config_manager = FoxyConfigManager(self._config_path)
        foxy_config = foxy_config_manager.load_config()
        if foxy_config.get("enable_harvester") is True:
            self._harvester_service = service_factory.make_harvester()

        self._chia_launcher = ChiaLauncher(foxy_root=self._foxy_root, config=config)
        await self._chia_launcher.run_with_daemon(self.start_and_await_services, quiet=True)

    async def start_and_await_services(self):
        # Do not log farmer id as it is not tracked yet
        # log.info(f"Farmer starting (id={self._farmer_service._node.server.node_id.hex()[:8]})")

        awaitables = [
            self._farmer_service.run(),
            self._chia_launcher.daemon_ws_server.shutdown_event.wait(),
        ]

        if self._harvester_service is not None:
            log.info(f"Harvester starting (id={self._harvester_service._node.server.node_id.hex()[:8]})")
            awaitables.append(self._harvester_service.run())

        await asyncio.gather(*awaitables)

    async def stop(self):
        if self._harvester_service is not None:
            self._harvester_service.stop()
        self._farmer_service.stop()
        await self._chia_launcher.daemon_ws_server.stop()

    async def _accept_signal(
        self,
        signal_: signal.Signals,
        stack_frame: Optional[FrameType],
        loop: asyncio.AbstractEventLoop,
    ) -> None:
        await self.stop()

    async def setup_process_global_state(self) -> None:
        async with SignalHandlers.manage() as signal_handlers:
            signal_handlers.setup_async_signal_handler(handler=self._accept_signal)


async def run_foxy_farmer(foxy_root: Path, config_path: Path):
    foxy_farmer = FoxyFarmer(foxy_root, config_path)
    await foxy_farmer.setup_process_global_state()
    await foxy_farmer.start()


@click.group(
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
@click.pass_context
def cli(ctx, config):
    ctx.ensure_object(dict)
    ctx.obj["root_path"] = Path(os.path.expanduser(os.getenv("FOXY_ROOT", "~/.foxy-farmer/mainnet"))).resolve()
    ctx.obj["config_path"] = Path(config).resolve()
    if ctx.invoked_subcommand is None:
        ctx.forward(run_cmd)


@cli.command("run", short_help="Run foxy-farmer, can be omitted")
@click.pass_context
def run_cmd(ctx, config):
    async_run(run_foxy_farmer(ctx.obj["root_path"], ctx.obj["config_path"]))


cli.add_command(summary_cmd)
cli.add_command(join_pool_cmd)
cli.add_command(authenticate_cmd)
cli.add_command(keys_cmd)
cli.add_command(plots_cmd)
cli.add_command(passphrase_cmd)


def main() -> None:
    cli()


if __name__ == '__main__':
    freeze_support()
    main()
