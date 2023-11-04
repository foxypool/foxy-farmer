from typing import List, Dict, Any, Tuple

from blspy import G1Element, G2Element, AugSchemeMPL
from chia.daemon.keychain_proxy import KeychainProxy
from chia.protocols.pool_protocol import get_current_authentication_token, AuthenticationPayload
from chia.types.blockchain_format.sized_bytes import bytes32
from chia.util.byte_types import hexstr_to_bytes
from chia.util.hash import std_hash
from chia.wallet.derive_keys import find_authentication_sk

from foxy_farmer.foundation.pool.pool_info import get_pool_info


async def generate_login_links(keychain_proxy: KeychainProxy, pool_list: List[Dict[str, Any]]) -> List[Tuple[str, str]]:
    all_root_sks = [sk for sk, _ in await keychain_proxy.get_all_private_keys()]

    login_links: List[Tuple[str, str]] = []
    for pool in pool_list:
        launcher_id = pool["launcher_id"]
        if pool.get("pool_url", "") == "":
            # Skip solo PlotNFT
            continue

        owner_public_key = G1Element.from_bytes(hexstr_to_bytes(pool["owner_public_key"]))
        authentication_sk = find_authentication_sk(all_root_sks, owner_public_key)
        if authentication_sk is None:
            print(f"The key for Launcher Id {launcher_id} does not seem to be added to this system yet, skipping ...")

            continue
        pool_url = pool["pool_url"]
        pool_info = await get_pool_info(pool_url)
        authentication_token_timeout = pool_info["authentication_token_timeout"]
        authentication_token = get_current_authentication_token(authentication_token_timeout)
        message: bytes32 = std_hash(
            AuthenticationPayload(
                "get_login",
                bytes32.from_hexstr(launcher_id),
                bytes32.from_hexstr(pool["target_puzzle_hash"]),
                authentication_token,
            )
        )
        signature: G2Element = AugSchemeMPL.sign(authentication_sk, message)
        login_link = f"{pool_url}/login?launcher_id={launcher_id}&authentication_token={authentication_token}&signature={bytes(signature).hex()}"

        login_links.append((launcher_id, login_link))

    return login_links
