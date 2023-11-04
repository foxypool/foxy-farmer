from typing import Dict, Any

from foxy_farmer.foundation.pool.pool_api_client import PoolApiClient
from foxy_farmer.foundation.util.memoize_async import MemoizeAsync


@MemoizeAsync
async def get_pool_info(pool_url: str) -> Dict[str, Any]:
    pool_api_client = PoolApiClient(pool_url=pool_url)

    return await pool_api_client.get_pool_info()
