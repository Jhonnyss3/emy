from decimal import Decimal, InvalidOperation

from django import template

register = template.Library()


@register.filter
def brl(value):
    """Format a number as Brazilian currency: 1234.5 -> 'R$ 1.234,56'."""
    try:
        amount = Decimal(value).quantize(Decimal("0.01"))
    except (TypeError, ValueError, InvalidOperation):
        return value
    integer, _, decimals = f"{abs(amount):.2f}".partition(".")
    groups = []
    while len(integer) > 3:
        groups.insert(0, integer[-3:])
        integer = integer[:-3]
    groups.insert(0, integer)
    formatted = ".".join(groups)
    sign = "-" if amount < 0 else ""
    return f"{sign}R$ {formatted},{decimals}"
