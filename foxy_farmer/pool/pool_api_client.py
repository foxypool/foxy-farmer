from typing import Dict, Any

from aiohttp import ClientSession, ClientTimeout

from foxy_farmer.util.ssl_context import ssl_context

TIMEOUT = ClientTimeout(total=30)
POOL_URL = "https://farmer-chia.foxypool.io"


class PoolApiClient:
    _pool_url: str

    def __init__(self, pool_url: str = POOL_URL):
        self._pool_url = pool_url

    async def get_pool_info(self) -> Dict[str, Any]:
        async with ClientSession(timeout=TIMEOUT) as client:
            async with client.get(f"{self._pool_url}/pool_info", ssl=ssl_context) as res:
                return await res.json()
