import json

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from activities.models import Activity, Category, Course, Review
from core.models import Wishlist

JEJU_REGION = "제주"

BANNER_TAGS_EN = ["Popular", "Featured", "Best", "HOT", "NEW"]
BANNER_TAGS_KO = ["인기", "추천", "특가", "HOT", "NEW"]


def _build_banners(lang="en"):
    qs = Activity.objects.filter(
        status=Activity.Status.APPROVED,
        region__name=JEJU_REGION,
        thumbnail_url__gt="",
        google_rating__gte=4.0,
    ).select_related("category", "region").order_by("?")[:5]

    tags = BANNER_TAGS_KO if lang == "ko" else BANNER_TAGS_EN
    banners = []
    for i, a in enumerate(qs):
        title = (a.title_ko or a.title) if lang == "ko" else a.title
        desc = (a.description_ko or a.description) if lang == "ko" else a.description
        if len(desc) > 60:
            desc = desc[:60] + "…"
        banners.append({
            "thumbnail_url": a.thumbnail_url,
            "tag": tags[i % len(tags)],
            "title": title,
            "description": desc,
            "activity_id": a.pk,
        })
    return banners


def home(request):
    categories = Category.objects.all()
    all_categories = ["All"] + list(categories.values_list("name", flat=True))
    from django.db.models import F, Value, FloatField, ExpressionWrapper
    from django.db.models.functions import Coalesce
    activities = Activity.objects.filter(
        status=Activity.Status.APPROVED,
        region__name=JEJU_REGION,
    ).select_related("category", "region").annotate(
        popularity=ExpressionWrapper(
            Coalesce(F("google_rating"), Value(0.0)) * (F("google_reviews_count") + 1),
            output_field=FloatField(),
        )
    ).order_by("-popularity")[:6]

    lang = request.COOKIES.get("lang", "en")
    courses = Course.objects.filter(is_active=True).prefetch_related("activities")[:6]
    banners = _build_banners(lang)

    return render(request, "core/home.html", {
        "categories": categories,
        "all_categories": all_categories,
        "activities": activities,
        "courses": courses,
        "banners": banners,
    })


def search(request):
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        results = Activity.objects.filter(
            status=Activity.Status.APPROVED,
            region__name=JEJU_REGION,
        ).filter(
            Q(title__icontains=query) |
            Q(address__icontains=query) |
            Q(category__name__icontains=query)
        ).select_related("category", "region")[:20]

    return render(request, "core/search.html", {
        "query": query,
        "results": results,
        "popular_keywords": ["Surfing", "Diving", "Kayaking", "Hiking", "Fishing", "Cycling"],
    })


@login_required
def wishlist(request):
    items = Wishlist.objects.filter(
        user=request.user
    ).select_related("activity__category", "activity__region").order_by("-created_at")
    categories = list(set(w.activity.category.name for w in items))
    categories.sort()
    return render(request, "core/wishlist.html", {"items": items, "categories": categories})


def profile(request):
    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next=/profile/")

    from bookings.models import Booking
    booking_count = Booking.objects.filter(user=request.user).count()
    review_count = Review.objects.filter(user=request.user).count()
    wishlist_count = Wishlist.objects.filter(user=request.user).count()

    return render(request, "core/profile.html", {
        "booking_count": booking_count,
        "review_count": review_count,
        "wishlist_count": wishlist_count,
    })


@login_required
@require_POST
def wishlist_toggle(request):
    try:
        data = json.loads(request.body)
        activity_id = int(data.get("activity_id", 0))
    except (json.JSONDecodeError, ValueError, TypeError):
        return JsonResponse({"error": "invalid"}, status=400)

    activity = Activity.objects.filter(pk=activity_id).first()
    if not activity:
        return JsonResponse({"error": "not found"}, status=404)

    obj, created = Wishlist.objects.get_or_create(
        user=request.user, activity=activity
    )
    if not created:
        obj.delete()

    return JsonResponse({"wished": created, "activity_id": activity_id})


@login_required
def wishlist_ids(request):
    ids = list(
        Wishlist.objects.filter(user=request.user).values_list("activity_id", flat=True)
    )
    return JsonResponse({"ids": ids})


@login_required
def profile_edit(request):
    user = request.user

    if request.method == "POST":
        first_name = request.POST.get("first_name", "").strip()
        last_name = request.POST.get("last_name", "").strip()
        phone = request.POST.get("phone", "").strip()

        user.first_name = first_name
        user.last_name = last_name
        update_fields = ["first_name", "last_name"]

        if hasattr(user, "phone"):
            user.phone = phone
            update_fields.append("phone")

        user.save(update_fields=update_fields)
        messages.success(request, "Profile updated successfully.")
        return redirect("core:profile")

    return render(request, "core/profile_edit.html")


@login_required
def my_reviews(request):
    reviews = Review.objects.filter(
        user=request.user
    ).select_related("activity__category", "activity__region").order_by("-created_at")

    return render(request, "core/my_reviews.html", {
        "reviews": reviews,
    })


def notifications(request):
    return render(request, "core/notifications.html")


def faq(request):
    return render(request, "core/faq.html")


def terms(request):
    return render(request, "core/terms.html")


def privacy(request):
    return render(request, "core/privacy.html")


def set_lang(request):
    lang = request.GET.get("lang", "en")
    if lang not in ("en", "ko"):
        lang = "en"
    referer = request.META.get("HTTP_REFERER", "/")
    response = redirect(referer)
    response.set_cookie("lang", lang, max_age=365 * 24 * 60 * 60, path="/", samesite="Lax")
    return response
