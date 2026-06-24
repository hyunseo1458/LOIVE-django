from django import template

register = template.Library()


@register.filter
def currency(value):
    try:
        return f"₩{int(value):,}"
    except (ValueError, TypeError):
        return value


@register.filter
def intcomma(value):
    try:
        return f"{int(value):,}"
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


HOURS_KO_TO_EN = {
    "월요일": "Mon", "화요일": "Tue", "수요일": "Wed",
    "목요일": "Thu", "금요일": "Fri", "토요일": "Sat", "일요일": "Sun",
    "오전": "AM", "오후": "PM", "휴무일": "Closed", "24시간 영업": "Open 24h",
}

HOURS_KO_SHORT = {
    "월요일": "월", "화요일": "화", "수요일": "수",
    "목요일": "목", "금요일": "금", "토요일": "토", "일요일": "일",
}


@register.filter
def loc_hours(hours_list, lang="en"):
    if not hours_list:
        return hours_list
    result = []
    for line in hours_list:
        if lang == "ko":
            for full, short in HOURS_KO_SHORT.items():
                line = line.replace(full, short)
        else:
            for ko, en in HOURS_KO_TO_EN.items():
                line = line.replace(ko, en)
        result.append(line)
    return result


@register.filter
def loc_reviews(obj, lang="en"):
    if lang == "ko":
        return obj.google_reviews or []
    return obj.google_reviews_en or obj.google_reviews or []


@register.filter
def loc_addr(obj, lang="en"):
    import re
    if lang == "ko":
        addr = getattr(obj, "address_ko", "") or obj.address
        for prefix in ["대한민국 ", "제주특별자치도 ", "특별자치도, ", "특별자치도 "]:
            addr = addr.replace(prefix, "")
    else:
        addr = obj.address
        for prefix in ["South Korea, ", "Jeju-do, ", "특별자치도, ", "특별자치도 "]:
            addr = addr.replace(prefix, "")
        addr = re.sub(r',\s*KR$', '', addr)
    return addr.strip(", ")
