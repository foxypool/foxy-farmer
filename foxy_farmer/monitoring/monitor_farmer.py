from asyncio import Event, sleep
from logging import getLogger
from pathlib import Path
from time import time
from typing import Any, List, Dict

from chia.cmds.cmds_util import get_any_service_client
from chia.rpc.farmer_rpc_client import FarmerRpcClient
from chia.server.outbound_message import NodeType


async def monitor_farmer(root_path: Path, until: Event):
    time_slept = 0
    while not until.is_set() and time_slept < 60:
        await sleep(1)
        time_slept += 1
    if until.is_set():
        return

    logger = getLogger("farmer_monitor")
    logger.info(f"Starting to monitor for stale connections")

    async with get_any_service_client(FarmerRpcClient, root_path=root_path) as (farmer_client, _):
        farmer_client: FarmerRpcClient

        async def get_stale_connections() -> List[Dict[str, Any]]:
            connections = await farmer_client.get_connections(node_type=NodeType.FULL_NODE)
            current_time = time()

            return [conn for conn in connections if current_time - conn.get("last_message_time", 0) >= 90]

        time_slept = 0
        while not until.is_set():
            if time_slept >= 10:
                time_slept = 0
                try:
                    stale_connections = await get_stale_connections()
                    for connection in stale_connections:
                        logger.warning(f"Detected stale connection to {connection['peer_host']}:{connection['peer_port']}, reconnecting ..")
                        # Will auto reconnect as the connections are in the default peers, we just need to close the connection
                        await farmer_client.close_connection(connection["node_id"])
                except Exception as e:
                    logger.error(f"Encountered an error while checking for stale connections: {e}")

            await sleep(1)
            time_slept += 1
