from typing import Any, Awaitable


async def await_done(awaitable: Awaitable[Any]):
    try:
        await awaitable
    except:
        pass
