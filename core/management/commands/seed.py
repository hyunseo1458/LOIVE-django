from django.core.management.base import BaseCommand
from django.utils import timezone
from accounts.models import User, Partner
from activities.models import Category, Region, Activity, ActivitySlot, Course

IMG = {
    "kayak": "https://lh3.googleusercontent.com/aida-public/AB6AXuAnLl5qtZieNSWnZNJWVAYcH4Ktkf7JmJcL0Xp4XSp82aYw8OYYs6kOXxhFaYjpSbI82eYD350q1MRi_xGVmerW-WPxkjBD5O52JiZspkNOb4KN2rwiw7fC0VmTMmhopmIqKBrAwBPaSrnNj5hOobrSCw3XuWjigv0bAoLsaqOsOcfU7OodxNqHPy0iBImG8ySZqjCmdyhA3J2tCtKsUTNVNlYOENNqNiQDmpbrERka8SPicL9HP20ltPcsDmcWEE_O8ajtgbsD06ee",
    "surf": "https://lh3.googleusercontent.com/aida-public/AB6AXuDU1gn1e7aVL1aaitRyIClIUHokRF4rj6Vfq8WutKd6Zi-qhGYo0MT_ufkFRgPDyaPoSKWNrPyFUNFcHd_YRE65BdNtyiuy-fJHXDzwl6t1pxKhJETAf6qZnzC-vMV_vMT9tLdjZevlRFBB9h4xfmiqh4I31xo03_ZUyX2kzAnYvmYIDsOqpk0Ll65Vi2PAC2hUeQSPNpOHlwDZoCkk9PP9nf0sa9NK09TOL_3YjO1Brc4hYGceldhIURxjP9LR8qBAE10Unlo_3uDS",
    "dive": "https://lh3.googleusercontent.com/aida-public/AB6AXuAlZLMA1X5ZiBabutTEeuZAK8roJWvOINmjBLrIIEEBBlRa7zqv7DqMZWvAoEQkG8uNWDACPXIpTU-OjPp0JjmKEnmJ8mCk_BiYluo22zmBjc6ubZV5CuuutDPHjimE9fyjOFAHkG4CHe4zieiVAKCAC8oekfMOg-Soqu4vZapK2s5ScK5EAwWqrA2ixSBmPlFAzKKzF2lnILOb7BdrmZKbKQjKTgyHYNSkMZ34HGG6ss_X7-D1WFsOulVPqoefeE5l6ARoLq3Lx67l",
    "trail": "https://lh3.googleusercontent.com/aida-public/AB6AXuCb87KLvzeu1cOmJaBeIjCtWqFM0LTCoWnHXvw7LKc1_fslTTnnkVagdE8Afsq72N8kRZtyUiDyxYMjeHBjiJsyhtwgEM_OIKlTOLe5VNPcBDx4ffU1gUNJDXiGu-M8SeCP-TMTWhuIhndghBCUjKAi1inLVNAO7qzLBf3m4VhEzKgwlPofWDSTXR3DCeYcG_QZGKspqca3QJPXGPVfWXzr6--4zcX9JRtKJfUi15j83Qr-fOR_oejzdleg0yYAvXFfuRopUh88KmBu",
    "mountain": "https://lh3.googleusercontent.com/aida-public/AB6AXuDi3EfEq1zLefrgPpxgoyGhAY3yiU7tfIZAWYdpkuj9Kh8xSU_Crz9HmtMfs2X9aii7Kfj2q_7_fo8JqwFFga0FKPr0XS0O0OcZ2U6GqLmKr4DaaiqiUgSRMrv-hHyL7nxRs-4MMyZeSc7eYsa6mgqHewBayMW6af6smkIWAKDfoi-tpGvejZxvntQ3tJI-152x7rWKCbPNn7KKZ6lREr2PkhxxcXM29Jr80gb8rq8tgqpnhzWpS4nl8tTgdOOi73LYC9SmKwqqhYyY",
}


class Command(BaseCommand):
    help = "Seed database with mock data matching the Next.js frontend"

    def handle(self, *args, **options):
        # Categories
        cats = {}
        for i, (name, slug) in enumerate([
            ("해양", "ocean"), ("자연", "nature"), ("문화", "culture"), ("음식", "food"), ("숙박", "stay"),
        ]):
            cats[slug], _ = Category.objects.get_or_create(name=name, defaults={"slug": slug, "order": i})

        # Regions
        regions = {}
        for name in ["서울", "경기", "인천", "강원", "충북", "충남", "대전", "전북", "전남", "광주", "경북", "경남", "대구", "울산", "부산", "제주"]:
            slug = name
            regions[name], _ = Region.objects.get_or_create(name=name, defaults={"slug": slug})

        # Partner user
        partner_user, created = User.objects.get_or_create(
            username="partner1",
            defaults={"email": "partner@loive.kr", "role": User.Role.PARTNER, "first_name": "로이브", "last_name": "파트너"},
        )
        if created:
            partner_user.set_password("partner1234")
            partner_user.save()

        partner, _ = Partner.objects.get_or_create(
            user=partner_user,
            defaults={
                "business_name": "로이브 체험",
                "business_number": "123-45-67890",
                "bank_name": "신한은행",
                "account_number": "110-123-456789",
                "account_holder": "로이브",
                "status": Partner.Status.APPROVED,
                "approved_at": timezone.now(),
            },
        )

        # Activities (matching Next.js mock data)
        activities_data = [
            {"title": "투명 카약 체험", "cat": "ocean", "region": "제주", "price": 45000, "loc": "애월 해안", "img": IMG["kayak"], "desc": "투명한 바다 위를 카약으로 누벼보세요. 맑은 날이면 바다 밑 산호초까지 보입니다."},
            {"title": "프리미엄 서핑 강습", "cat": "ocean", "region": "제주", "price": 60000, "loc": "중문 색달 해변", "img": IMG["surf"], "desc": "전문 강사와 함께하는 2시간 서핑 강습. 초보자도 환영합니다."},
            {"title": "해녀 체험 다이빙", "cat": "ocean", "region": "제주", "price": 80000, "loc": "우도", "img": IMG["dive"], "desc": "우도에서 즐기는 정통 해녀 체험. 장비 일체 포함."},
            {"title": "해운대 서핑 클래스", "cat": "ocean", "region": "부산", "price": 55000, "loc": "해운대 해변", "img": IMG["kayak"], "desc": "해운대에서 즐기는 서핑. 보드와 웻슈트 제공."},
            {"title": "감천문화마을 투어", "cat": "culture", "region": "부산", "price": 25000, "loc": "감천문화마을", "img": IMG["surf"], "desc": "다채로운 건물과 골목길을 걸으며 부산의 예술을 만나보세요."},
            {"title": "태종대 트레킹", "cat": "nature", "region": "부산", "price": 15000, "loc": "태종대", "img": IMG["dive"], "desc": "부산 남단의 아름다운 해안 절벽을 따라 걸어보세요."},
            {"title": "속초 서핑 체험", "cat": "ocean", "region": "강원", "price": 50000, "loc": "속초 해변", "img": IMG["trail"], "desc": "동해안의 파도에서 즐기는 서핑 체험."},
            {"title": "설악산 등산 투어", "cat": "nature", "region": "강원", "price": 35000, "loc": "설악산", "img": IMG["mountain"], "desc": "전문 가이드와 함께하는 설악산 등산."},
            {"title": "강릉 커피거리 투어", "cat": "culture", "region": "강원", "price": 20000, "loc": "강릉 안목해변", "img": IMG["kayak"], "desc": "안목해변의 유명 카페들을 순회하는 커피 투어."},
            {"title": "통영 루지 체험", "cat": "nature", "region": "경남", "price": 18000, "loc": "통영 스카이라인", "img": IMG["surf"], "desc": "통영 스카이라인 루지를 타며 바다를 내려다보세요."},
            {"title": "남해 독일마을 산책", "cat": "culture", "region": "경남", "price": 10000, "loc": "남해 독일마을", "img": IMG["dive"], "desc": "이국적인 독일마을에서 여유로운 산책을 즐겨보세요."},
            {"title": "북촌 한옥마을 투어", "cat": "culture", "region": "서울", "price": 30000, "loc": "북촌", "img": IMG["trail"], "desc": "전통 한옥의 아름다움을 만끽하는 가이드 투어."},
            {"title": "한강 카약 체험", "cat": "ocean", "region": "서울", "price": 40000, "loc": "여의도 한강공원", "img": IMG["mountain"], "desc": "도심 속 한강에서 즐기는 카약 체험."},
            {"title": "남산 둘레길 트레킹", "cat": "nature", "region": "서울", "price": 15000, "loc": "남산", "img": IMG["kayak"], "desc": "서울 중심의 남산 둘레길을 걸으며 도시 전경을 감상하세요."},
            {"title": "가평 레일바이크", "cat": "nature", "region": "경기", "price": 30000, "loc": "가평", "img": IMG["surf"], "desc": "아름다운 북한강변을 따라 달리는 레일바이크."},
            {"title": "수원화성 야간 투어", "cat": "culture", "region": "경기", "price": 20000, "loc": "수원화성", "img": IMG["dive"], "desc": "유네스코 세계유산 수원화성의 아름다운 야경 투어."},
        ]

        from datetime import date, time, timedelta

        for data in activities_data:
            activity, created = Activity.objects.get_or_create(
                title=data["title"],
                defaults={
                    "partner": partner,
                    "category": cats[data["cat"]],
                    "region": regions[data["region"]],
                    "price": data["price"],
                    "capacity": 20,
                    "duration_minutes": 120,
                    "address": data["loc"],
                    "description": data["desc"],
                    "thumbnail_url": data["img"],
                    "status": Activity.Status.APPROVED,
                },
            )
            if created:
                today = date.today()
                for d in range(7):
                    for t in [time(9, 0), time(13, 0), time(16, 0)]:
                        ActivitySlot.objects.create(
                            activity=activity,
                            date=today + timedelta(days=d),
                            start_time=t,
                            remaining=activity.capacity,
                        )

        # Courses
        jeju_activities = Activity.objects.filter(region__name="제주")[:3]
        course1, _ = Course.objects.get_or_create(
            title="동부 해안 힐링 로드",
            defaults={
                "description": "한적한 산책로와 해변 카페, 바다 옆 요가 클래스.",
                "price": 150000,
                "image": "",
            },
        )
        course1.activities.set(jeju_activities)

        busan_activities = Activity.objects.filter(region__name="부산")[:3]
        course2, _ = Course.objects.get_or_create(
            title="럭셔리 요트 투어",
            defaults={
                "description": "선셋 세일링, 프리미엄 다이닝과 돌고래 와칭.",
                "price": 200000,
                "image": "",
            },
        )
        course2.activities.set(busan_activities)

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: {Activity.objects.count()} activities, "
            f"{ActivitySlot.objects.count()} slots, "
            f"{Course.objects.count()} courses"
        ))
