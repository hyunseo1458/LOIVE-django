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


@register.simple_tag(takes_context=True)
def t(context, en, ko):
    return ko if context.get("LANG") == "ko" else en


CATEGORY_KO = {
    "All": "전체",
    "Surfing": "서핑",
    "Diving": "다이빙",
    "Kayak / SUP": "카약 / SUP",
    "Jet Ski": "제트스키",
    "Parasailing": "패러글라이딩",
    "Hiking": "등산",
    "ATV / Buggy": "ATV / 버기",
    "Horse Riding": "승마",
    "Fishing": "낚시",
    "Cycling": "자전거",
}


@register.filter
def cat_name(value, lang="en"):
    if lang == "ko":
        return CATEGORY_KO.get(value, value)
    return value


@register.filter
def loc(obj, lang="en"):
    if lang == "ko":
        return getattr(obj, "title_ko", "") or obj.title
    return obj.title


@register.filter
def loc_desc(obj, lang="en"):
    if lang == "ko":
        return getattr(obj, "description_ko", "") or obj.description
    return obj.description


@register.filter
def loc_addr(obj, lang="en"):
    if lang == "ko":
        return getattr(obj, "address_ko", "") or obj.address
    return obj.address
