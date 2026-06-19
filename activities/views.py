from urllib.parse import unquote

from django.shortcuts import render, get_object_or_404, redirect
from django.db import transaction
from django.db.models import Avg, Count, Q
from .models import Activity, Category, Course, Region, Review


def explore(request):
    category_slug = request.GET.get("category", "")
    query = request.GET.get("q", "").strip()
    sort = request.GET.get("sort", "추천순")
    region_name = unquote(request.COOKIES.get("region", ""))

    activities = Activity.objects.filter(
        status=Activity.Status.APPROVED
    ).select_related("category", "region").annotate(
        avg_rating=Avg("reviews__rating"),
        review_count=Count("reviews"),
    )

    if region_name:
        activities = activities.filter(region__name=region_name)

    if query:
        activities = activities.filter(
            Q(title__icontains=query) |
            Q(address__icontains=query) |
            Q(category__name__icontains=query)
        )
    if category_slug:
        activities = activities.filter(category__slug=category_slug)

    if sort == "평점 높은순":
        activities = activities.order_by("-avg_rating")
    elif sort == "가격 낮은순":
        activities = activities.order_by("price")
    elif sort == "가격 높은순":
        activities = activities.order_by("-price")

    categories = Category.objects.all()

    return render(request, "activities/explore.html", {
        "activities": activities,
        "categories": categories,
        "current_category": category_slug,
        "current_query": query,
        "current_region": region_name,
        "current_sort": sort,
        "sort_options": ["추천순", "평점 높은순", "가격 낮은순", "가격 높은순"],
    })


def detail(request, pk):
    activity = get_object_or_404(
        Activity.objects.select_related("category", "region", "partner"),
        pk=pk, status=Activity.Status.APPROVED,
    )
    reviews = activity.reviews.select_related("user").order_by("-created_at")[:5]
    review_stats = activity.reviews.aggregate(
        avg=Avg("rating"), count=Count("id"),
    )
    slots = activity.slots.filter(remaining__gt=0).order_by("date", "start_time")[:21]
    related = Activity.objects.filter(
        category=activity.category, status=Activity.Status.APPROVED
    ).exclude(pk=pk)[:4]

    return render(request, "activities/detail.html", {
        "activity": activity,
        "reviews": reviews,
        "review_avg": review_stats["avg"] or 0,
        "review_count": review_stats["count"],
        "slots": slots,
        "related": related,
    })


def reviews(request, pk):
    activity = get_object_or_404(Activity, pk=pk)
    review_list = activity.reviews.select_related("user").order_by("-created_at")
    review_stats = activity.reviews.aggregate(
        avg=Avg("rating"), count=Count("id"),
    )
    total = review_stats["count"] or 1
    star_dist = {}
    for s in range(1, 6):
        cnt = activity.reviews.filter(rating=s).count()
        star_dist[s] = {"count": cnt, "pct": round(cnt / total * 100)}

    return render(request, "activities/reviews.html", {
        "activity": activity,
        "reviews": review_list,
        "review_avg": review_stats["avg"] or 0,
        "review_count": review_stats["count"],
        "star_dist": star_dist,
    })


def write_review(request, pk):
    from bookings.models import Booking
    from django.contrib import messages

    activity = get_object_or_404(Activity, pk=pk)

    if not request.user.is_authenticated:
        return redirect(f"/accounts/login/?next=/activities/{pk}/review/")

    has_completed = Booking.objects.filter(
        user=request.user,
        slot__activity=activity,
        status=Booking.Status.COMPLETED,
    ).exists()

    if not has_completed:
        messages.error(request, "이용 완료된 예약이 있어야 리뷰를 작성할 수 있습니다.")
        return redirect("activities:reviews", pk=pk)

    if request.method == "POST":
        try:
            rating = int(request.POST.get("rating", 5))
        except (ValueError, TypeError):
            rating = 5
        rating = max(1, min(5, rating))
        content = request.POST.get("content", "")
        if content.strip():
            with transaction.atomic():
                Review.objects.update_or_create(
                    activity=activity, user=request.user,
                    defaults={"rating": rating, "content": content},
                )
            return redirect("activities:reviews", pk=pk)

    return render(request, "activities/write_review.html", {
        "activity": activity,
    })


def course_detail(request, pk):
    course = get_object_or_404(
        Course.objects.prefetch_related(
            "activities__category", "activities__region"
        ),
        pk=pk, is_active=True,
    )
    activities = course.activities.filter(
        status=Activity.Status.APPROVED
    ).select_related("category", "region").annotate(
        avg_rating=Avg("reviews__rating"),
        review_count=Count("reviews"),
    )
    return render(request, "activities/course_detail.html", {
        "course": course,
        "activities": activities,
    })
