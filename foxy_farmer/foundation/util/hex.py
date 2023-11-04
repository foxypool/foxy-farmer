def ensure_hex_prefix(string: str) -> str:
    return string if string.startswith("0x") else f"0x{string}"
