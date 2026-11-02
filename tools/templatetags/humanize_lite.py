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


@register.filter
def duration(seconds: int) -> str:
    """12 -> '12 sec', 75 -> '1 min 15 sec', 600 -> '10 min'."""
    seconds = int(seconds)
    if seconds < 60:
        return f"{seconds} sec"
    minutes, rest = divmod(seconds, 60)
    return f"{minutes} min" if rest == 0 or minutes >= 10 else f"{minutes} min {rest} sec"
