from decimal import Decimal

from foxy_farmer.foundation.util.decimal import is_valid_decimal


def is_valid_fee(amount_raw: str):
    if not is_valid_decimal(amount_raw):
        return False
    amount = Decimal(amount_raw)

    return amount >= 0
