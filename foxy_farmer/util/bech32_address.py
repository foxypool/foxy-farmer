from chia.util.bech32m import decode_puzzle_hash


def is_valid_address(address: str) -> bool:
    try:
        decode_puzzle_hash(address)
    except ValueError:
        return False

    return True
