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
    help = "Seed database with Jeju outdoor activity data"

    def handle(self, *args, **options):
        # --- Categories: Jeju outdoor/marine activity types ---
        cats = {}
        cat_defs = [
            ("Surfing", "surfing", 0),
            ("Diving", "diving", 1),
            ("Kayak / SUP", "kayak", 2),
            ("Jet Ski", "jet-ski", 3),
            ("Parasailing", "parasailing", 4),
            ("Hiking", "hiking", 5),
            ("ATV / Buggy", "atv", 6),
            ("Horse Riding", "horse-riding", 7),
            ("Fishing", "fishing", 8),
            ("Cycling", "cycling", 9),
        ]
        for name, slug, order in cat_defs:
            cats[slug], _ = Category.objects.update_or_create(slug=slug, defaults={"name": name, "order": order})

        # --- Regions (keep all for future expansion) ---
        regions = {}
        for name in ["서울", "경기", "인천", "강원", "충북", "충남", "대전", "전북", "전남", "광주", "경북", "경남", "대구", "울산", "부산", "제주"]:
            regions[name], _ = Region.objects.get_or_create(name=name, defaults={"slug": name})

        # --- Partner user ---
        partner_user, created = User.objects.get_or_create(
            username="partner1",
            defaults={"email": "partner@loive.kr", "role": User.Role.PARTNER, "first_name": "LOIVE", "last_name": "Partner"},
        )
        if created:
            partner_user.set_password("partner1234")
            partner_user.save()

        partner, _ = Partner.objects.get_or_create(
            user=partner_user,
            defaults={
                "business_name": "LOIVE Jeju",
                "business_number": "123-45-67890",
                "bank_name": "Shinhan",
                "account_number": "110-123-456789",
                "account_holder": "LOIVE",
                "status": Partner.Status.APPROVED,
                "approved_at": timezone.now(),
            },
        )

        # --- Jeju outdoor activities ---
        jeju = regions["제주"]
        activities_data = [
            {
                "title": "Jungmun Beach Surfing Lesson", "title_ko": "중문 해변 서핑 강습",
                "cat": "surfing", "price": 60000, "duration": 120,
                "address": "Jungmun Saekdal Beach, Seogwipo", "address_ko": "서귀포시 중문 색달해변",
                "lat": "33.2436", "lng": "126.4108", "img": IMG["surf"],
                "desc": "Catch your first wave at Jungmun Beach! 2-hour beginner-friendly lesson with all equipment included.",
                "desc_ko": "중문 해변에서 첫 파도를 잡아보세요! 초보자 맞춤 2시간 강습, 장비 전부 포함.",
            },
            {
                "title": "Woljeongri Beach Surf Experience", "title_ko": "월정리 해변 서핑 체험",
                "cat": "surfing", "price": 55000, "duration": 120,
                "address": "Woljeong-ri Beach, Gujwa-eup", "address_ko": "제주시 구좌읍 월정리 해변",
                "lat": "33.5560", "lng": "126.8040", "img": IMG["surf"],
                "desc": "Ride the waves at Jeju's most iconic beach. Crystal-clear turquoise water, perfect for beginners.",
                "desc_ko": "제주 월정리 해변에서 서핑을 즐겨보세요. 투명한 에메랄드빛 바다, 초보자도 OK.",
            },
            {
                "title": "Udo Island Snorkeling & Diving", "title_ko": "우도 스노클링 & 다이빙",
                "cat": "diving", "price": 80000, "duration": 180,
                "address": "Udo Island, Jeju", "address_ko": "제주시 우도면",
                "lat": "33.5067", "lng": "126.9519", "img": IMG["dive"],
                "desc": "Explore the underwater world around Udo Island. All gear provided. No experience necessary.",
                "desc_ko": "우도 바다 속 세계를 탐험하세요. 장비 전부 제공, 경험 없어도 OK.",
            },
            {
                "title": "Seogwipo Scuba Diving", "title_ko": "서귀포 문섬 스쿠버 다이빙",
                "cat": "diving", "price": 95000, "duration": 180,
                "address": "Munseom Island, Seogwipo", "address_ko": "서귀포시 문섬 해역",
                "lat": "33.2290", "lng": "126.5650", "img": IMG["dive"],
                "desc": "Dive into UNESCO-protected waters of Munseom. PADI-certified instructors for all levels.",
                "desc_ko": "유네스코 보호 해역 문섬에서 다이빙. PADI 인증 강사, 모든 레벨 환영.",
            },
            {
                "title": "Aewol Clear Kayak Tour", "title_ko": "애월 투명 카약 투어",
                "cat": "kayak", "price": 45000, "duration": 90,
                "address": "Aewol Coastal Road, Jeju", "address_ko": "제주시 애월읍 해안도로",
                "lat": "33.4620", "lng": "126.3250", "img": IMG["kayak"],
                "desc": "Paddle a transparent kayak over Aewol's crystal-clear waters.",
                "desc_ko": "애월의 투명한 바다 위를 투명 카약으로 누벼보세요.",
            },
            {
                "title": "Hallasan Summit Hiking", "title_ko": "한라산 정상 등반",
                "cat": "hiking", "price": 40000, "duration": 480,
                "address": "Hallasan National Park", "address_ko": "제주시 한라산국립공원",
                "lat": "33.3617", "lng": "126.5292", "img": IMG["mountain"],
                "desc": "Conquer South Korea's highest peak (1,950m). Full-day guided hike.",
                "desc_ko": "대한민국 최고봉(1,950m) 한라산 종일 가이드 등반.",
            },
            {
                "title": "Jeju Olle Trail Walk (Route 7)", "title_ko": "제주 올레길 7코스 걷기",
                "cat": "hiking", "price": 25000, "duration": 240,
                "address": "Olle Trail Route 7, Seogwipo", "address_ko": "서귀포시 올레길 7코스",
                "lat": "33.2528", "lng": "126.4116", "img": IMG["trail"],
                "desc": "Walk the most scenic section of Jeju Olle Trail. Coastal cliffs and hidden beaches.",
                "desc_ko": "제주 올레길에서 가장 아름다운 구간. 해안 절벽과 숨겨진 해변.",
            },
            {
                "title": "Chagwido Boat Fishing", "title_ko": "차귀도 선상 낚시",
                "cat": "fishing", "price": 70000, "duration": 240,
                "address": "Chagwido Island, Hallim", "address_ko": "제주시 한림읍 차귀도",
                "lat": "33.3139", "lng": "126.1528", "img": IMG["trail"],
                "desc": "Deep-sea fishing around Chagwido Island. All tackle and bait provided.",
                "desc_ko": "차귀도 근해 선상 낚시. 낚시 장비·미끼 전부 제공.",
            },
            {
                "title": "East Coast Scenic Cycling", "title_ko": "동부 해안 자전거 투어",
                "cat": "cycling", "price": 30000, "duration": 180,
                "address": "Woljeongri to Sehwa Beach", "address_ko": "월정리 ~ 세화해변 해안도로",
                "lat": "33.4500", "lng": "126.9200", "img": IMG["trail"],
                "desc": "Cycle along Jeju's stunning east coast. Bike rental, helmet, and route map included.",
                "desc_ko": "제주 동부 해안을 따라 자전거를 타세요. 자전거·헬멧·지도 포함.",
            },
            {
                "title": "Jeju Jet Ski Experience", "title_ko": "제주 제트스키 체험",
                "cat": "jet-ski", "price": 50000, "duration": 30,
                "address": "Iho Tewoo Beach, Jeju", "address_ko": "제주시 이호테우해변",
                "lat": "33.4970", "lng": "126.4530", "img": IMG["surf"],
                "desc": "Ride jet skis on Jeju's beautiful Iho Beach. Thrilling speed on the ocean.",
                "desc_ko": "이호해변에서 제트스키를 타세요. 바다 위 스릴 만점 체험.",
            },
            {
                "title": "Jeju ATV Off-Road Adventure", "title_ko": "제주 ATV 오프로드 체험",
                "cat": "atv", "price": 45000, "duration": 60,
                "address": "Hallim ATV Park, Jeju", "address_ko": "제주시 한림읍 ATV 체험장",
                "lat": "33.3800", "lng": "126.2700", "img": IMG["mountain"],
                "desc": "Off-road ATV adventure through Jeju's volcanic terrain and forests.",
                "desc_ko": "제주 화산 지형과 숲을 가로지르는 ATV 오프로드 체험.",
            },
            {
                "title": "Jeju Horse Riding by the Sea", "title_ko": "제주 해변 승마 체험",
                "cat": "horse-riding", "price": 55000, "duration": 60,
                "address": "Hallim Riding Club, Jeju", "address_ko": "제주시 한림읍 승마클럽",
                "lat": "33.4000", "lng": "126.2500", "img": IMG["trail"],
                "desc": "Ride horses along Jeju's beautiful coastline. Beginner-friendly, guided tour.",
                "desc_ko": "제주 해안을 따라 말을 타세요. 초보자 가능, 가이드 동행.",
            },
        ]

        from datetime import date, time, timedelta

        for data in activities_data:
            activity, created = Activity.objects.update_or_create(
                title=data["title"],
                defaults={
                    "partner": partner,
                    "category": cats[data["cat"]],
                    "region": jeju,
                    "price": data["price"],
                    "capacity": 12,
                    "duration_minutes": data["duration"],
                    "address": data["address"],
                    "address_ko": data["address_ko"],
                    "latitude": data["lat"],
                    "longitude": data["lng"],
                    "description": data["desc"],
                    "title_ko": data["title_ko"],
                    "description_ko": data["desc_ko"],
                    "thumbnail_url": data["img"],
                    "status": Activity.Status.APPROVED,
                },
            )
            if created:
                today = date.today()
                for d in range(14):
                    for t in [time(9, 0), time(13, 0), time(16, 0)]:
                        ActivitySlot.objects.create(
                            activity=activity,
                            date=today + timedelta(days=d),
                            start_time=t,
                            remaining=activity.capacity,
                        )

        # --- Curated courses ---
        surf_activities = Activity.objects.filter(category__slug="surfing", region=jeju)[:2]
        course1, _ = Course.objects.update_or_create(
            title="Jeju Ocean Adventure Day",
            defaults={
                "title_ko": "제주 해양 어드벤처 데이",
                "description": "Surf in the morning, kayak at sunset. The ultimate Jeju water sports combo.",
                "description_ko": "아침엔 서핑, 석양엔 카약. 제주 해양 스포츠 풀코스.",
                "price": 95000,
                "image": "",
            },
        )
        course1.activities.set(surf_activities)

        hike_activities = Activity.objects.filter(category__slug="hiking", region=jeju)[:2]
        course2, _ = Course.objects.update_or_create(
            title="Jeju Nature Explorer",
            defaults={
                "title_ko": "제주 자연 탐험 코스",
                "description": "Summit Hallasan and walk the Olle Trail. Two days of Jeju's best landscapes.",
                "description_ko": "한라산 정상 등반 + 올레길 걷기. 제주 최고의 자연경관 이틀 코스.",
                "price": 60000,
                "image": "",
            },
        )
        course2.activities.set(hike_activities)

        self.stdout.write(self.style.SUCCESS(
            f"Seed complete: {Activity.objects.count()} activities, "
            f"{ActivitySlot.objects.count()} slots, "
            f"{Course.objects.count()} courses"
        ))
