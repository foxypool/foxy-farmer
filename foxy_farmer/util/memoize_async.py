from typing import Callable, TypeVar, Generic, Dict

ArgType = TypeVar('ArgType')
ResultType = TypeVar('ResultType')


class MemoizeAsync(Generic[ArgType, ResultType]):
    _async_fn: Callable[[ArgType], ResultType]
    _cache: Dict[ArgType, ResultType] = {}

    def __init__(self, async_fn: Callable[[ArgType], ResultType]):
        self._async_fn = async_fn

    async def __call__(self, arg: ArgType) -> ResultType:
        if arg not in self._cache:
            self._cache[arg] = await self._async_fn(arg)
        return self._cache[arg]
