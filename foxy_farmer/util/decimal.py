from decimal import Decimal


def is_valid_decimal(amount: str) -> bool:
    try:
        Decimal(amount)
    except Exception:
        return False

    return True
