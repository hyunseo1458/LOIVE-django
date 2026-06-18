from urllib.parse import unquote

from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.db.models import Q, Avg, Count
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from activities.models import Activity, Category, Course, Region, Review

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


def wishlist(request):
    return render(request, "core/wishlist.html")


def profile(request):
    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next=/profile/")

    from bookings.models import Booking
    booking_count = Booking.objects.filter(user=request.user).count()
    review_count = Review.objects.filter(user=request.user).count()

    return render(request, "core/profile.html", {
        "booking_count": booking_count,
        "review_count": review_count,
    })


def wishlist_api(request):
    ids_param = request.GET.get("ids", "")
    if not ids_param.strip():
        return JsonResponse([], safe=False)

    try:
        ids = [int(x.strip()) for x in ids_param.split(",") if x.strip()]
    except (ValueError, TypeError):
        return JsonResponse([], safe=False)

    activities = Activity.objects.filter(
        pk__in=ids, status=Activity.Status.APPROVED
    ).select_related("category", "region")

    data = []
    for a in activities:
        data.append({
            "id": a.pk,
            "title": a.title,
            "price": a.price,
            "thumbnail_url": a.thumbnail_url or "",
            "region": a.region.name if a.region else "",
            "category": a.category.name if a.category else "",
            "rating_avg": float(a.rating_avg),
        })
    return JsonResponse(data, safe=False)


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


def notifications(request):
    return render(request, "core/notifications.html")


def faq(request):
    return render(request, "core/faq.html")


def terms(request):
    return render(request, "core/terms.html")


def privacy(request):
    return render(request, "core/privacy.html")
