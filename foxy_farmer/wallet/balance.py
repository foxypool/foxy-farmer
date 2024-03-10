from asyncio import sleep
from decimal import Decimal
from typing import Callable

from chia.cmds.units import units
from chia.rpc.wallet_rpc_client import WalletRpcClient
from yaspin import yaspin


async def ensure_balance(required_balance_mojo: int, message_while_waiting_closure: Callable[[Decimal], str], wallet_client: WalletRpcClient):
    balances = await wallet_client.get_wallet_balance(1)
    balance = balances["confirmed_wallet_balance"]
    remaining = required_balance_mojo - balance
    if remaining <= 0:
        return
    remaining_xch = Decimal(remaining) / units["chia"]
    message_while_waiting = message_while_waiting_closure(remaining_xch)
    with yaspin(text=message_while_waiting) as spinner:
        while balance < required_balance_mojo:
            await sleep(1)
            balances = await wallet_client.get_wallet_balance(1)
            balance = balances["confirmed_wallet_balance"]
            remaining = required_balance_mojo - balance
            remaining_xch = Decimal(remaining) / units["chia"]
            spinner.text = message_while_waiting_closure(remaining_xch)
