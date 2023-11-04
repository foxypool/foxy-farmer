from asyncio import sleep
from datetime import datetime

from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.server.outbound_message import NodeType
from humanize import naturaldelta
from yaspin import yaspin


async def wait_for_wallet_sync(wallet_client: WalletRpcClient):
    with yaspin(text="Waiting for the wallet to sync ...") as spinner:
        async def update_spinner_text():
            connected_full_nodes_count = len(await wallet_client.get_connections(node_type=NodeType.FULL_NODE))
            wallet_height = await wallet_client.get_height_info()
            relative_time = "N/A"
            if connected_full_nodes_count > 0:
                try:
                    wallet_timestamp = await wallet_client.get_timestamp_for_height(wallet_height)
                    relative_time = naturaldelta(datetime.now() - datetime.fromtimestamp(float(wallet_timestamp)))
                except:
                    pass
                spinner.text = f"Waiting for the wallet to sync (peers={connected_full_nodes_count}, height={wallet_height}, {relative_time} behind) ..."

        while len(await wallet_client.get_connections(node_type=NodeType.FULL_NODE)) < 2:
            await update_spinner_text()
            await sleep(5)
        await update_spinner_text()
        await sleep(10)
        while await wallet_client.get_sync_status():
            await update_spinner_text()
            await sleep(5)
        while not (await wallet_client.get_synced()):
            await update_spinner_text()
            await sleep(5)
    print("✅ Wallet synced")
