from django import template

register = template.Library()


@register.filter
def num(value: int) -> str:
    """1234 -> '1,234'."""
    return f"{int(value):,}"


@register.filter
def delta(after: int, before: int) -> str:
    """Signed change from before to after, using a real minus sign: '−12' or '+3'."""
    diff = int(after) - int(before)
    return f"+{diff:,}" if diff > 0 else f"−{abs(diff):,}"
