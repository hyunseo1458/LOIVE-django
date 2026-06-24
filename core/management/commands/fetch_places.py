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

                    raw_name = place.get("name", "")
                    data = {
                        "category": cats[slug],
                        "region": jeju,
                        "title": raw_name,
                        "title_ko": self._clean_ko_name(raw_name),
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

        if not dry_run:
            self._enrich_details(api_key)
            self._enrich_english(api_key)

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
        ).exclude(google_place_id="")

        self.stdout.write(f"\nEnriching all details for {activities.count()} places...")
        for i, activity in enumerate(activities):
            url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                "place_id": activity.google_place_id,
                "fields": "formatted_phone_number,website,photos,opening_hours,reviews",
                "key": api_key,
                "language": "ko",
            }
            try:
                resp = requests.get(url, params=params, timeout=10)
                result = resp.json().get("result", {})

                activity.phone = result.get("formatted_phone_number", "") or ""
                activity.website = result.get("website", "") or ""

                hours = result.get("opening_hours", {})
                activity.opening_hours = hours.get("weekday_text", [])

                reviews = result.get("reviews", [])
                clean_reviews = []
                for r in reviews[:5]:
                    clean_reviews.append({
                        "author": r.get("author_name", ""),
                        "rating": r.get("rating", 0),
                        "text": r.get("text", ""),
                        "time": r.get("relative_time_description", ""),
                        "photo": r.get("profile_photo_url", ""),
                    })
                activity.google_reviews = clean_reviews

                photos = result.get("photos", [])
                photo_urls = []
                for p in photos[:20]:
                    ref = p.get("photo_reference")
                    if ref:
                        photo_urls.append(
                            f"https://maps.googleapis.com/maps/api/place/photo"
                            f"?maxwidth=800&photo_reference={ref}&key={api_key}"
                        )
                if photo_urls:
                    activity.photo_urls = photo_urls
                    activity.thumbnail_url = photo_urls[0]

                activity.save(update_fields=[
                    "phone", "website", "photo_urls", "thumbnail_url",
                    "opening_hours", "google_reviews",
                ])

                if (i + 1) % 50 == 0:
                    self.stdout.write(f"  {i + 1}/{activities.count()} enriched...")
            except Exception as e:
                self.stderr.write(f"  Error enriching {activity.pk}: {e}")

    def _enrich_english(self, api_key):
        import re
        import time

        activities = Activity.objects.filter(
            google_place_id__isnull=False,
        ).exclude(google_place_id="")

        # Step 1: Fetch English names from Google Places API
        self.stdout.write(f"\nFetching English names for {activities.count()} places...")
        count = 0
        for activity in activities:
            url = "https://maps.googleapis.com/maps/api/place/details/json"
            params = {
                "place_id": activity.google_place_id,
                "fields": "name,formatted_address",
                "key": api_key,
                "language": "en",
            }
            try:
                resp = requests.get(url, params=params, timeout=10)
                result = resp.json().get("result", {})
                en_name = result.get("name", "")
                en_addr = result.get("formatted_address", "")
                if en_name:
                    activity.title = en_name
                if en_addr:
                    activity.address = en_addr
                activity.save(update_fields=["title", "address"])
                count += 1
            except Exception:
                pass
        self.stdout.write(f"  Updated {count} places with English names")

        # Step 2: Translate remaining Korean-only names
        self._translate_remaining()

    def _translate_remaining(self):
        import re
        import time

        needs_translation = []
        for a in Activity.objects.exclude(google_place_id="").exclude(google_place_id__isnull=True):
            if self._is_korean(a.title):
                needs_translation.append(a)

        if not needs_translation:
            self.stdout.write("  No Korean-only names to translate")
            return

        self.stdout.write(f"\nTranslating {len(needs_translation)} Korean-only names...")

        # First try to extract English from parentheses
        extracted = 0
        still_need = []
        for a in needs_translation:
            en = self._extract_english_from_name(a.title_ko)
            if en:
                a.title = en
                a.save(update_fields=["title"])
                extracted += 1
            else:
                still_need.append(a)

        self.stdout.write(f"  Extracted English from parentheses: {extracted}")

        # Then use deep-translator for the rest
        if still_need:
            self.stdout.write(f"  Translating {len(still_need)} remaining...")
            try:
                from deep_translator import GoogleTranslator
                translator = GoogleTranslator(source="ko", target="en")
                translated = 0
                for a in still_need:
                    try:
                        result = translator.translate(a.title_ko)
                        if result and result != a.title_ko:
                            a.title = result
                            a.save(update_fields=["title"])
                            translated += 1
                        time.sleep(0.5)
                    except Exception as e:
                        self.stderr.write(f"  Error translating '{a.title_ko}': {e}")
                        time.sleep(2)
                self.stdout.write(f"  Translated: {translated}")
            except ImportError:
                self.stderr.write("  deep-translator not installed: pip install deep-translator")

    @staticmethod
    def _is_korean(text):
        if not text:
            return False
        korean_chars = sum(1 for c in text if '가' <= c <= '힣')
        return korean_chars > len(text) * 0.3

    @staticmethod
    def _clean_ko_name(name):
        import re
        name = re.sub(r'\s*\([A-Za-z][\w\s&\-\.\']*\)', '', name)
        name = name.split('|')[0].strip()
        parts = name.split(' / ')
        if len(parts) > 1:
            best = max(parts, key=lambda p: sum(1 for c in p if '가' <= c <= '힣'))
            if sum(1 for c in best if '가' <= c <= '힣') > 0:
                name = best.strip()
        parts = name.split(' - ')
        if len(parts) > 1:
            best = max(parts, key=lambda p: sum(1 for c in p if '가' <= c <= '힣'))
            if sum(1 for c in best if '가' <= c <= '힣') > 0:
                name = best.strip()
        return name.strip()

    @staticmethod
    def _extract_english_from_name(name):
        import re
        match = re.search(r'\(([A-Za-z][\w\s&\-\.\']+)\)', name)
        if match:
            en = match.group(1).strip()
            if len(en) >= 3:
                return en
        parts = re.split(r'[/|]', name)
        for part in parts:
            part = part.strip()
            ascii_ratio = sum(1 for c in part if c.isascii() and c.isalpha()) / max(len(part), 1)
            if ascii_ratio > 0.6 and len(part) >= 3:
                return part
        return None
