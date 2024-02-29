from asyncio import sleep
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncIterator, Dict, Any, Optional

from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.util.ints import uint16
from yaspin import yaspin

from foxy_farmer.environment.embedded_chia_environment import EmbeddedChiaEnvironment


@asynccontextmanager
async def run_wallet(root_path: Path, config: Dict[str, Any]) -> AsyncIterator[WalletRpcClient]:
    chia_environment = EmbeddedChiaEnvironment(
        root_path=root_path,
        config=config,
        allow_connecting_to_existing_daemon=True,
    )
    wallet_rpc: Optional[WalletRpcClient] = None
    try:
        await chia_environment.start_daemon()
        await chia_environment.start_services(["wallet"])

        wallet_rpc = await WalletRpcClient.create(
            config["self_hostname"],
            uint16(config["wallet"]["rpc_port"]),
            root_path,
            config,
        )

        async def is_wallet_reachable() -> bool:
            try:
                await wallet_rpc.healthz()

                return True
            except:
                return False

        with yaspin(text="Waiting for the wallet to finish starting ..."):
            while not await is_wallet_reachable():
                await sleep(3)

        yield wallet_rpc
    finally:
        if wallet_rpc is not None:
            wallet_rpc.close()
            await wallet_rpc.await_closed()
        await chia_environment.stop_services(["wallet"])
        await chia_environment.stop_daemon()
