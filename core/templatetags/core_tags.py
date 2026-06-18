from django import template

register = template.Library()


@register.filter
def currency(value):
    try:
        return f"₩{int(value):,}"
    except (ValueError, TypeError):
        return value


@register.filter
def split(value, sep=","):
    return value.split(sep)
