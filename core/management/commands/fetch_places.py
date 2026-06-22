import requests
from django.core.management.base import BaseCommand
from django.conf import settings
from activities.models import Activity, Category, Region

JEJU_CENTER = {"lat": 33.3617, "lng": 126.5292}
SEARCH_RADIUS = 30000

CATEGORY_QUERIES = {
    "surfing": ["서핑 제주", "surfing jeju"],
    "diving": ["다이빙 제주", "스노클링 제주", "diving jeju"],
    "kayak": ["카약 제주", "SUP 제주", "kayak jeju"],
    "jet-ski": ["제트스키 제주", "바나나보트 제주", "jet ski jeju"],
    "parasailing": ["패러글라이딩 제주", "parasailing jeju"],
    "hiking": ["등산 제주 투어", "올레길", "hiking jeju"],
    "atv": ["ATV 제주", "버기카 제주"],
    "horse-riding": ["승마 제주", "horse riding jeju"],
    "fishing": ["낚시 제주", "fishing jeju"],
    "cycling": ["자전거 대여 제주", "cycling jeju"],
}


class Command(BaseCommand):
    help = "Fetch Jeju outdoor activity businesses from Google Places API"

    def add_arguments(self, parser):
        parser.add_argument("--category", type=str, help="Fetch only one category slug")
        parser.add_argument("--dry-run", action="store_true", help="Print results without saving")

    def handle(self, *args, **options):
        api_key = getattr(settings, "GOOGLE_PLACES_API_KEY", "")
        if not api_key:
            self.stderr.write(self.style.ERROR(
                "GOOGLE_PLACES_API_KEY not set in .env"
            ))
            return

        jeju, _ = Region.objects.get_or_create(name="제주", defaults={"slug": "제주"})

        cats = {}
        cat_defs = [
            ("Surfing", "surfing", "서핑", 0),
            ("Diving", "diving", "다이빙", 1),
            ("Kayak / SUP", "kayak", "카약 / SUP", 2),
            ("Jet Ski", "jet-ski", "제트스키", 3),
            ("Parasailing", "parasailing", "패러글라이딩", 4),
            ("Hiking", "hiking", "등산", 5),
            ("ATV / Buggy", "atv", "ATV / 버기", 6),
            ("Horse Riding", "horse-riding", "승마", 7),
            ("Fishing", "fishing", "낚시", 8),
            ("Cycling", "cycling", "자전거", 9),
        ]
        for name, slug, name_ko, order in cat_defs:
            cat, created = Category.objects.update_or_create(
                slug=slug, defaults={"name": name, "order": order}
            )
            cats[slug] = cat

        target_slug = options.get("category")
        dry_run = options.get("dry_run", False)
        total_created = 0
        total_updated = 0

        for slug, queries in CATEGORY_QUERIES.items():
            if target_slug and slug != target_slug:
                continue
            if slug not in cats:
                continue

            self.stdout.write(f"\n--- {cats[slug].name} ---")

            for query in queries:
                places = self._search_places(api_key, query)
                self.stdout.write(f"  '{query}': {len(places)} results")

                for place in places:
                    place_id = place.get("place_id")
                    if not place_id:
                        continue

                    loc = place.get("geometry", {}).get("location", {})
                    photos = place.get("photos", [])
                    photo_urls = []
                    for p in photos[:5]:
                        ref = p.get("photo_reference")
                        if ref:
                            photo_urls.append(
                                f"https://maps.googleapis.com/maps/api/place/photo"
                                f"?maxwidth=800&photo_reference={ref}&key={api_key}"
                            )

                    data = {
                        "category": cats[slug],
                        "region": jeju,
                        "title": place.get("name", ""),
                        "title_ko": place.get("name", ""),
                        "address": place.get("vicinity", "") or place.get("formatted_address", ""),
                        "address_ko": place.get("vicinity", "") or place.get("formatted_address", ""),
                        "latitude": loc.get("lat"),
                        "longitude": loc.get("lng"),
                        "google_rating": place.get("rating"),
                        "google_reviews_count": place.get("user_ratings_total", 0),
                        "thumbnail_url": photo_urls[0] if photo_urls else "",
                        "photo_urls": photo_urls,
                        "status": Activity.Status.APPROVED,
                    }

                    if dry_run:
                        try:
                            self.stdout.write(f"    [DRY] {data['title']} ({data['google_rating']})")
                        except UnicodeEncodeError:
                            self.stdout.write(f"    [DRY] (name encode error) ({data['google_rating']})")
                        continue

                    _, created = Activity.objects.update_or_create(
                        google_place_id=place_id,
                        defaults=data,
                    )
                    if created:
                        total_created += 1
                    else:
                        total_updated += 1

        # Fetch phone/website details for new entries without phone
        if not dry_run:
            self._enrich_details(api_key)

        self.stdout.write(self.style.SUCCESS(
            f"\nDone: {total_created} created, {total_updated} updated, "
            f"{Activity.objects.count()} total"
        ))

    def _search_places(self, api_key, query):
        url = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "location": f"{JEJU_CENTER['lat']},{JEJU_CENTER['lng']}",
            "radius": SEARCH_RADIUS,
            "key": api_key,
            "language": "ko",
        }
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            return data.get("results", [])
        except Exception as e:
            self.stderr.write(f"  Error: {e}")
            return []

    def _enrich_details(self, api_key):
        activities = Activity.objects.filter(
            google_place_id__isnull=False,
            phone="",
        ).exclude(google_place_id="")[:50]

        for activity in activities:
            url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                "place_id": activity.google_place_id,
                "fields": "formatted_phone_number,website,opening_hours",
                "key": api_key,
                "language": "ko",
            }
            try:
                resp = requests.get(url, params=params, timeout=10)
                result = resp.json().get("result", {})
                activity.phone = result.get("formatted_phone_number", "")
                activity.website = result.get("website", "")
                activity.save(update_fields=["phone", "website"])
            except Exception:
                pass
