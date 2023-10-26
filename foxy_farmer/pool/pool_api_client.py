from ssl import SSLContext

from aiohttp import ClientSession, ClientTimeout
from chia.server.server import ssl_context_for_root
from chia.ssl.create_ssl import get_mozilla_ca_crt

timeout = ClientTimeout(total=30)

POOL_URL = "https://farmer.chia.foxypool.io"


class PoolApiClient:
    _ssl_context: SSLContext = ssl_context_for_root(get_mozilla_ca_crt())
    _pool_url: str

    def __init__(self, pool_url: str = POOL_URL):
        self._pool_url = pool_url

    async def get_pool_info(self):
        async with ClientSession(timeout=timeout) as client:
            async with client.get(f"{self._pool_url}/pool_info", ssl=self._ssl_context) as res:
                return await res.json()
