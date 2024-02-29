from asyncio import sleep
from time import time
from typing import Awaitable, Dict, Any

from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.wallet.transaction_record import TransactionRecord


async def await_transaction_broadcasted(transaction_coro: Awaitable[Dict[str, Any]], wallet_client: WalletRpcClient):
    result = await transaction_coro
    tx_record: TransactionRecord = result["transaction"]
    start = time()
    while time() - start < 15:
        await sleep(0.1)
        tx = await wallet_client.get_transaction(1, tx_record.name)
        if len(tx.sent_to) > 0:
            return None
