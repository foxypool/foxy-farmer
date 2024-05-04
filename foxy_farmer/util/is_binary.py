import sys


def is_binary() -> bool:
    return getattr(sys, 'frozen', False)
