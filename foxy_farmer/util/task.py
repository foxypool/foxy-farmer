from asyncio import Task, CancelledError
from typing import Any


async def await_task_done(task: Task[Any]):
    try:
        await task
    except CancelledError:
        pass
