from urllib.parse import unquote

import json

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.views.decorators.http import require_POST
from activities.models import Activity, Category, Course, Region, Review
from core.models import Wishlist

BANNER_TAGS = ["인기", "추천", "특가", "HOT", "NEW"]


def _build_banners(region_name=""):
    qs = Activity.objects.filter(
        status=Activity.Status.APPROVED,
        thumbnail_url__gt="",
    ).select_related("category", "region")

    if region_name:
        qs = qs.filter(region__name=region_name)

    qs = qs.annotate(avg_rating=Avg("reviews__rating")).order_by("-avg_rating", "-created_at")[:5]

    banners = []
    for i, a in enumerate(qs):
        desc = a.description
        if len(desc) > 40:
            desc = desc[:40] + "…"
        banners.append({
            "thumbnail_url": a.thumbnail_url,
            "tag": BANNER_TAGS[i % len(BANNER_TAGS)],
            "title": a.title,
            "description": f"{desc} 1인 ₩{a.price:,}~",
            "activity_id": a.pk,
        })
    return banners


def home(request):
    categories = Category.objects.all()
    all_categories = ["전체"] + list(categories.values_list("name", flat=True))
    activities = Activity.objects.filter(
        status=Activity.Status.APPROVED
    ).select_related("category", "region")

    cookie_region = unquote(request.COOKIES.get("region", ""))
    if cookie_region and Region.objects.filter(name=cookie_region).exists():
        activities = activities.filter(region__name=cookie_region)

    activities = activities[:6]
    courses = Course.objects.filter(is_active=True).prefetch_related("activities")[:6]
    banners = _build_banners(cookie_region)
    if not banners:
        banners = _build_banners("")

    return render(request, "core/home.html", {
        "categories": categories,
        "all_categories": all_categories,
        "activities": activities,
        "courses": courses,
        "banners": banners,
        "current_region": cookie_region,
    })


def search(request):
    query = request.GET.get("q", "").strip()
    results = []
    if query:
        results = Activity.objects.filter(
            status=Activity.Status.APPROVED
        ).filter(
            Q(title__icontains=query) |
            Q(address__icontains=query) |
            Q(category__name__icontains=query) |
            Q(region__name__icontains=query)
        ).select_related("category", "region")[:20]

    return render(request, "core/search.html", {
        "query": query,
        "results": results,
        "popular_keywords": ["제주", "서핑", "카약", "부산", "강원", "트레킹"],
    })


@login_required
def wishlist(request):
    items = Wishlist.objects.filter(
        user=request.user
    ).select_related("activity__category", "activity__region").order_by("-created_at")
    return render(request, "core/wishlist.html", {"items": items})


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
        messages.success(request, "프로필이 성공적으로 업데이트되었습니다.")
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
