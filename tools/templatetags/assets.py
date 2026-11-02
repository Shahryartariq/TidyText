from django import template
from django.conf import settings
from django.templatetags.static import static

register = template.Library()


@register.simple_tag
def asset(path: str) -> str:
    """Static URL with a build id, so browsers fetch fresh files after each deploy."""
    return f"{static(path)}?v={settings.BUILD_ID}"
