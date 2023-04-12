import foxy_farmer.monkey_patch_chia_version
import asyncio
import functools
import logging
import os
import signal
import sys
from pathlib import Path
from types import FrameType
from typing import Optional

import click
import pkg_resources
from chia.daemon.server import WebSocketServer
from chia.farmer.farmer import Farmer
from chia.harvester.harvester import Harvester
from chia.server.start_service import async_run, Service

from chia.util.config import load_config

from foxy_farmer.farm_summary import summary_cmd
from foxy_farmer.foxy_chia_config_manager import FoxyChiaConfigManager
from foxy_farmer.foxy_config_manager import FoxyConfigManager
from foxy_farmer.gateway_availability_monitor import GatewayAvailabilityMonitor
from foxy_farmer.foxy_farmer_logging import initialize_logging_with_stdout
from foxy_farmer.service_factory import ServiceFactory

log = logging.getLogger("foxy_farmer")
version = pkg_resources.require("foxy-farmer")[0].version


class FoxyFarmer:
    _foxy_root: Path = Path(os.path.expanduser(os.getenv("FOXY_ROOT", "~/.foxy-farmer/mainnet"))).resolve()
    _config_path: Path
    _daemon_ws_server: WebSocketServer
    _farmer_service: Service[Farmer]
    _harvester_service: Optional[Service[Harvester]] = None
    _gateway_availability_monitor: GatewayAvailabilityMonitor

    def __init__(self, config_path: Path):
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
        self._daemon_ws_server = service_factory.make_daemon()
        self._farmer_service = service_factory.make_farmer()

        foxy_config_manager = FoxyConfigManager(self._config_path)
        foxy_config = foxy_config_manager.load_config()
        if foxy_config.get("enable_harvester") is True:
            self._harvester_service = service_factory.make_harvester()

        self._gateway_availability_monitor = GatewayAvailabilityMonitor(self._farmer_service)

        async with self._daemon_ws_server.run():
            awaitables = [
                self._farmer_service.run(),
                self._daemon_ws_server.shutdown_event.wait(),
            ]
            if self._harvester_service is not None:
                awaitables.append(self._harvester_service.run())

            self._gateway_availability_monitor.start()

            await asyncio.gather(*awaitables)

    def stop(self):
        self._gateway_availability_monitor.stop()
        if self._harvester_service is not None:
            self._harvester_service.stop()
        self._farmer_service.stop()
        asyncio.create_task(self._daemon_ws_server.stop())

    def _accept_signal(self, signal_number: int, stack_frame: Optional[FrameType] = None) -> None:
        self.stop()

    async def setup_process_global_state(self) -> None:
        if sys.platform == "win32" or sys.platform == "cygwin":
            # pylint: disable=E1101
            signal.signal(signal.SIGBREAK, self._accept_signal)
            signal.signal(signal.SIGINT, self._accept_signal)
            signal.signal(signal.SIGTERM, self._accept_signal)
        else:
            loop = asyncio.get_running_loop()
            loop.add_signal_handler(
                signal.SIGINT,
                functools.partial(self._accept_signal, signal_number=signal.SIGINT)
            )
            loop.add_signal_handler(
                signal.SIGTERM,
                functools.partial(self._accept_signal, signal_number=signal.SIGTERM)
            )


async def run_foxy_farmer(config_path: Path):
    foxy_farmer = FoxyFarmer(config_path)
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
    if ctx.invoked_subcommand is None:
        ctx.forward(run_cmd)


@cli.command("run", short_help="Run foxy-farmer, can be omitted")
@click.option(
    '-c',
    '--config',
    default='foxy-farmer.yaml',
    help="Config file path",
    type=click.Path(),
    show_default=True
)
def run_cmd(config: str):
    async_run(run_foxy_farmer(Path(config)))


cli.add_command(summary_cmd)


def main() -> None:
    cli()


if __name__ == '__main__':
    main()
