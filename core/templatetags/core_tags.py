from django import template

register = template.Library()


@register.filter
def currency(value):
    try:
        return f"₩{int(value):,}"
    except (ValueError, TypeError):
        return value


@register.simple_tag
def photo_url(url, activity=None):
    import base64
    if url and "googleapis.com" in url:
        encoded = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
        aid = activity.pk if activity and hasattr(activity, "pk") else "shared"
        return f"/api/photo/{encoded}/?aid={aid}"
    return url


@register.filter
def photo_proxy(url):
    import base64
    if url and "googleapis.com" in url:
        encoded = base64.urlsafe_b64encode(url.encode()).decode().rstrip("=")
        return f"/api/photo/{encoded}/"
    return url


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
    "Other": "기타",
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


CATEGORY_VIBE_EN = {
    "Surfing": {
        "intro": "🏄 Ready to catch your first wave? Jeju's ocean is calling!",
        "high": "🔥 One of Jeju's highest-rated surf spots — this is THE place to be!",
        "mid": "Whether you're a total beginner or a seasoned pro, the waves here are pure magic ✨",
        "features": "🎯 Pro instructors, top gear, warm water — all you need is your sense of adventure!",
    },
    "Diving": {
        "intro": "🤿 Plunge into Jeju's magical underwater kingdom!",
        "high": "🌟 One of the island's top-rated dive spots — it's THAT good!",
        "mid": "Sea turtles, neon corals, tropical fish — it's like swimming inside a documentary 🐠",
        "features": "🎯 Full gear, certified guides, zero experience needed. Just bring your curiosity!",
    },
    "Kayak / SUP": {
        "intro": "🚣 Paddle through paradise — Jeju's waters are unreal!",
        "high": "💙 A top-rated paddling experience — the views are absolutely unreal!",
        "mid": "Crystal-clear water, volcanic cliffs, hidden sea caves — it's a whole vibe 🌊",
        "features": "🎯 Everything provided. Perfect date, family outing, or solo escape!",
    },
    "Jet Ski": {
        "intro": "🚀 Full throttle on Jeju's wide open ocean!",
        "high": "⚡ Jeju's ultimate water thrill — pure adrenaline on the waves!",
        "mid": "Wind in your hair, spray on your face, island views all around 🌴",
        "features": "🎯 Quick safety intro, then GO! No license needed for guided rides.",
    },
    "Parasailing": {
        "intro": "🪂 Float above Jeju — the view will blow your mind!",
        "high": "😱 Jeju's most breathtaking aerial adventure — unforgettable!",
        "mid": "Hallasan, the ocean, the entire island — all at your feet from the sky 🌏",
        "features": "🎯 Experienced pilots, safe harness, and THE most Instagrammable moment ever 📸",
    },
    "Hiking": {
        "intro": "🥾 Lace up — Jeju's nature is about to blow you away!",
        "high": "🏆 A must-walk trail that keeps everyone coming back!",
        "mid": "Ancient forests, dramatic cliffs, hidden waterfalls — every step is a postcard 🌿",
        "features": "🎯 Well-marked trails, epic photo spots, and that fresh Jeju air!",
    },
    "ATV / Buggy": {
        "intro": "🏎️ Off-road madness through Jeju's volcanic wilderness!",
        "high": "🔥 Jeju's wildest off-road ride — the time of your life!",
        "mid": "Mud, dust, forest trails, ocean views — this is pure ADVENTURE 💨",
        "features": "🎯 Zero experience? No problem! Full safety gear + quick training included.",
    },
    "Horse Riding": {
        "intro": "🐴 Gallop through Jeju's green fields with the sea breeze!",
        "high": "❤️ A magical horseback experience you won't forget!",
        "mid": "Imagine: you, a gentle horse, green pastures, Hallasan in the background 🌄",
        "features": "🎯 Friendly horses, expert guides. Beginners & families totally welcome!",
    },
    "Fishing": {
        "intro": "🎣 Drop your line into Jeju's crystal blue waters!",
        "high": "🐟 The fish are always biting here — Jeju's go-to fishing spot!",
        "mid": "Deep-sea thrill or chill shore fishing — pick your vibe and reel it in 🌅",
        "features": "🎯 All gear provided. Catch something? They'll cook it for you! 🍳",
    },
    "Cycling": {
        "intro": "🚴 Wind in your hair, ocean by your side — let's ride Jeju!",
        "high": "🌟 Jeju's best cycling route — the ride of a lifetime!",
        "mid": "Wind turbines, stone walls, turquoise bays — every turn is a wow moment 😍",
        "features": "🎯 Bike, helmet, map all included. E-bike option for easy cruising!",
    },
}

CATEGORY_VIBE_KO = {
    "Surfing": {
        "intro": "🏄 제주 바다가 부른다! 첫 파도를 잡을 준비 되셨나요?",
        "high": "🔥 제주 서핑 핫플 중의 핫플! 여기 아니면 어디?",
        "mid": "완전 초보도, 서핑 고수도 모두 즐거운 제주의 파도 ✨",
        "features": "🎯 전문 강사, 최신 장비, 따뜻한 바다 — 모험심만 가져오세요!",
    },
    "Diving": {
        "intro": "🤿 제주 바다 속 마법의 세계로 풍덩!",
        "high": "🌟 한번 빠지면 헤어나올 수 없는 제주 바다 속 세상!",
        "mid": "바다거북, 형형색색 산호, 열대어 — 다큐멘터리 속에 들어온 느낌 🐠",
        "features": "🎯 장비 전부 제공, 자격증 강사. 경험 없어도 걱정 NO!",
    },
    "Kayak / SUP": {
        "intro": "🚣 제주의 에메랄드 바다 위를 떠다니는 꿈 같은 시간!",
        "high": "💙 이 풍경 앞에서 감탄이 절로 나오는 곳!",
        "mid": "투명한 바다, 화산 절벽, 숨겨진 해식동굴 — 이게 바로 힐링 🌊",
        "features": "🎯 장비 전부 포함. 데이트, 가족여행, 혼자 힐링 모두 완벽!",
    },
    "Jet Ski": {
        "intro": "🚀 제주 바다 위에서 전속력으로 달려보자!",
        "high": "⚡ 제주 바다 위 최고의 스릴! 한번 타면 멈출 수 없어요!",
        "mid": "시원한 바람, 튀는 물보라, 눈앞에 펼쳐진 제주 해안선 🌴",
        "features": "🎯 안전 교육 후 바로 출발! 가이드 동행 시 면허 불필요.",
    },
    "Parasailing": {
        "intro": "🪂 하늘에서 보는 제주, 상상 그 이상입니다!",
        "high": "😱 하늘에서 보는 제주는 차원이 달라요! 감동 보장!",
        "mid": "한라산, 바다, 섬 전체가 발 아래에 — 말로 표현 불가 🌏",
        "features": "🎯 베테랑 파일럿, 안전 장비 완비. 인생샷은 덤! 📸",
    },
    "Hiking": {
        "intro": "🥾 신발 끈 묶고 출발! 제주 자연이 반겨줍니다!",
        "high": "🏆 한번 걸으면 또 오고 싶은 제주 최고의 코스!",
        "mid": "원시림, 절벽, 숨은 폭포 — 한 걸음마다 엽서 같은 풍경 🌿",
        "features": "🎯 잘 정비된 탐방로, 곳곳의 포토 스팟, 그리고 제주의 맑은 공기!",
    },
    "ATV / Buggy": {
        "intro": "🏎️ 제주의 화산 지형을 미친 듯이 달려보자!",
        "high": "🔥 인생 체험 각! 제주 오프로드의 끝판왕!",
        "mid": "흙먼지, 숲길, 해안 뷰 — 이건 진짜 모험이다 💨",
        "features": "🎯 처음이어도 OK! 안전 장비 + 기초 교육 완비.",
    },
    "Horse Riding": {
        "intro": "🐴 제주 초원에서 말과 함께하는 로맨틱한 시간!",
        "high": "❤️ 말 위에서 느끼는 제주의 바람, 잊지 못할 추억!",
        "mid": "순한 말, 푸른 초원, 한라산 배경 — 영화 속 한 장면 🌄",
        "features": "🎯 친절한 말, 전문 가이드. 초보자도 가족도 모두 환영!",
    },
    "Fishing": {
        "intro": "🎣 제주 바다의 풍요로움을 낚아올려 보세요!",
        "high": "🐟 손맛 보장! 제주 바다의 풍요로움을 직접 느껴보세요!",
        "mid": "짜릿한 선상 낚시든, 여유로운 갯바위 낚시든 — 취향대로 🌅",
        "features": "🎯 장비 전부 제공. 잡은 물고기 바로 회 떠준대요! 🍣",
    },
    "Cycling": {
        "intro": "🚴 바람을 가르며 제주 해안을 달리는 상쾌함!",
        "high": "🌟 페달 밟는 순간 알게 돼요, 이게 인생 라이딩이구나!",
        "mid": "풍력발전기, 돌담, 에메랄드 해변 — 페달 밟을 때마다 감탄 😍",
        "features": "🎯 자전거, 헬멧, 지도 전부 포함. 전동 자전거도 있어요!",
    },
}


@register.filter
def auto_desc(obj, lang="en"):
    desc_en = getattr(obj, "description", "") or ""
    desc_ko = getattr(obj, "description_ko", "") or ""
    is_spot = desc_en == "SPOT"

    if not is_spot:
        desc = desc_ko if lang == "ko" else desc_en
        if desc:
            return desc

    cat = obj.category.name if hasattr(obj, "category") else ""
    rating = float(getattr(obj, "google_rating", 0) or 0)
    reviews = int(getattr(obj, "google_reviews_count", 0) or 0)
    is_business = not is_spot

    vibes = CATEGORY_VIBE_KO.get(cat, {}) if lang == "ko" else CATEGORY_VIBE_EN.get(cat, {})

    if not vibes:
        if lang == "ko":
            return "🌴 제주에서 즐기는 특별한 체험. 자세한 정보는 업체에 직접 문의해주세요."
        return "🌴 A unique experience in Jeju. Contact the business for more details."

    parts = [vibes["intro"]]
    if rating >= 4.5 and reviews >= 10:
        parts.append(vibes["high"])
    else:
        parts.append(vibes["mid"])

    if is_business:
        parts.append(vibes["features"])
    else:
        if lang == "ko":
            parts.append("📍 자연 명소입니다. 방문 전 현지 상황을 확인해주세요.")
        else:
            parts.append("📍 This is a natural spot. Check local conditions before visiting.")

    return " ".join(parts)


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
