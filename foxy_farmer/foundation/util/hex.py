def ensure_hex_prefix(string: str) -> str:
    return string if string.startswith("0x") else f"0x{string}"


def strip_hex_prefix(string: str) -> str:
    return string[2:] if string.startswith("0x") else string
