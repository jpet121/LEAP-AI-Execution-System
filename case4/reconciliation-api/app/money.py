"""Strict cent syntax with context-independent arithmetic."""
import re
from decimal import Decimal, localcontext

MAX = Decimal('999999999.99')

def money(value: str, *, positive: bool = False) -> str:
    if not isinstance(value, str) or re.fullmatch(r'[0-9]+\.[0-9]{2}', value) is None:
        raise ValueError('Expected an unsigned decimal string with exactly two fractional digits')
    amount = Decimal(value)
    if amount > MAX or (positive and amount == 0):
        raise ValueError('Amount outside permitted range')
    return format(amount, '.2f')

def changed(balance: str, amount: str, kind: str) -> str:
    with localcontext() as context:
        context.prec = 32
        result = Decimal(balance) + (Decimal(amount) if kind == 'CREDIT' else -Decimal(amount))
    if result < 0 or result > MAX:
        raise ValueError('Result outside permitted balance range')
    return format(result, '.2f')
