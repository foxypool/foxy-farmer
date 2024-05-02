from asyncio import sleep
from time import time
from typing import Awaitable, Dict, Any, Union

from chia.rpc.wallet_rpc_client import WalletRpcClient
from chia.wallet.transaction_record import TransactionRecord


async def await_transaction_broadcasted(
        transaction_coro: Awaitable[Union[Dict[str, Any], TransactionRecord]],
        wallet_client: WalletRpcClient,
) -> TransactionRecord:
    result = await transaction_coro
    tx_record: TransactionRecord = result if isinstance(result, TransactionRecord) else result["transaction"]
    start = time()
    while time() - start < 15:
        await sleep(0.5)
        tx = await wallet_client.get_transaction(tx_record.name)
        if len(tx.sent_to) > 0:
            return tx_record


async def await_transaction_confirmed(transaction_record: TransactionRecord, wallet_client: WalletRpcClient) -> None:
    while not transaction_record.confirmed:
        await sleep(0.5)
        transaction_record = await wallet_client.get_transaction(transaction_record.name)
