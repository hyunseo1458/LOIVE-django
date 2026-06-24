from django.conf import settings


def lang(request):
    return {
        "LANG": request.COOKIES.get("lang", "en"),
        "GA_MEASUREMENT_ID": settings.GA_MEASUREMENT_ID,
        "GOOGLE_PLACES_API_KEY": settings.GOOGLE_PLACES_API_KEY,
    }
