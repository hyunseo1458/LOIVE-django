from functools import wraps
from datetime import date

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Sum, Count, Avg, Q
from django.utils import timezone

from accounts.models import Partner
from activities.models import Activity, ActivitySlot, Category, Region
from bookings.models import Booking
from settlements.models import Settlement


# ---------------------------------------------------------------------------
# Access-control decorator
# ---------------------------------------------------------------------------

def partner_required(view_func):
    """Login + partner/staff 권한 확인 데코레이터"""
    @wraps(view_func)
    @login_required
    def _wrapped(request, *args, **kwargs):
        if not (request.user.is_partner or request.user.is_staff):
            messages.error(request, "파트너 권한이 필요합니다.")
            return redirect("core:home")
        # partner_profile 존재 확인
        try:
            request.user.partner_profile
        except Partner.DoesNotExist:
            messages.error(request, "파트너 프로필이 등록되지 않았습니다. 관리자에게 문의하세요.")
            return redirect("core:home")
        return view_func(request, *args, **kwargs)
    return _wrapped


def _partner(request):
    """현재 유저의 Partner 인스턴스 반환 헬퍼"""
    return request.user.partner_profile


# ---------------------------------------------------------------------------
# 1. Dashboard
# ---------------------------------------------------------------------------

@partner_required
def dashboard(request):
    partner = _partner(request)
    today = timezone.now().date()
    month_start = today.replace(day=1)

    # 파트너의 모든 액티비티 PK
    activity_ids = Activity.objects.filter(partner=partner).values_list("pk", flat=True)

    # 총 예약 건수
    total_bookings = Booking.objects.filter(
        slot__activity__partner=partner,
    ).exclude(status=Booking.Status.CANCELLED).count()

    # 이번 달 매출
    monthly_sales = Booking.objects.filter(
        slot__activity__partner=partner,
        status__in=[Booking.Status.CONFIRMED, Booking.Status.COMPLETED],
        created_at__date__gte=month_start,
    ).aggregate(total=Sum("total_amount"))["total"] or 0

    # 등록 액티비티 수
    activity_count = Activity.objects.filter(partner=partner).count()

    # 평균 평점
    avg_rating = Activity.objects.filter(
        partner=partner,
    ).aggregate(avg=Avg("reviews__rating"))["avg"] or 0

    # 최근 예약 10건
    recent_bookings = Booking.objects.filter(
        slot__activity__partner=partner,
    ).select_related(
        "user", "slot__activity",
    ).order_by("-created_at")[:10]

    return render(request, "partner/dashboard.html", {
        "partner": partner,
        "total_bookings": total_bookings,
        "monthly_sales": monthly_sales,
        "activity_count": activity_count,
        "avg_rating": round(avg_rating, 1),
        "recent_bookings": recent_bookings,
    })


# ---------------------------------------------------------------------------
# 2. Activity List
# ---------------------------------------------------------------------------

@partner_required
def activity_list(request):
    partner = _partner(request)
    status_filter = request.GET.get("status", "")

    activities = Activity.objects.filter(
        partner=partner,
    ).select_related("category").order_by("-created_at")

    if status_filter and status_filter in dict(Activity.Status.choices):
        activities = activities.filter(status=status_filter)

    status_counts = dict(
        Activity.objects.filter(partner=partner)
        .values_list("status")
        .annotate(cnt=Count("id"))
        .values_list("status", "cnt")
    )
    total_count = sum(status_counts.values())

    return render(request, "partner/activity_list.html", {
        "activities": activities,
        "current_status": status_filter,
        "status_choices": Activity.Status.choices,
        "status_counts": status_counts,
        "total_count": total_count,
    })


# ---------------------------------------------------------------------------
# 3. Activity Create / Edit
# ---------------------------------------------------------------------------

@partner_required
def activity_create(request):
    categories = Category.objects.all()
    regions = Region.objects.all()

    if request.method == "POST":
        partner = _partner(request)
        activity = Activity.objects.create(
            partner=partner,
            title=request.POST.get("title", ""),
            category_id=request.POST.get("category"),
            region_id=request.POST.get("region"),
            description=request.POST.get("description", ""),
            price=int(request.POST.get("price", 0)),
            capacity=int(request.POST.get("capacity", 1)),
            duration_minutes=int(request.POST.get("duration_minutes", 60)),
            address=request.POST.get("address", ""),
            thumbnail_url=request.POST.get("thumbnail_url", ""),
            status=Activity.Status.DRAFT,
        )
        messages.success(request, f"'{activity.title}' 액티비티가 등록되었습니다.")
        return redirect("partner:activity_list")

    return render(request, "partner/activity_form.html", {
        "categories": categories,
        "regions": regions,
        "editing": False,
    })


@partner_required
def activity_edit(request, pk):
    partner = _partner(request)
    activity = get_object_or_404(Activity, pk=pk, partner=partner)
    categories = Category.objects.all()
    regions = Region.objects.all()

    if request.method == "POST":
        activity.title = request.POST.get("title", activity.title)
        activity.category_id = request.POST.get("category", activity.category_id)
        activity.region_id = request.POST.get("region", activity.region_id)
        activity.description = request.POST.get("description", activity.description)
        activity.price = int(request.POST.get("price", activity.price))
        activity.capacity = int(request.POST.get("capacity", activity.capacity))
        activity.duration_minutes = int(request.POST.get("duration_minutes", activity.duration_minutes))
        activity.address = request.POST.get("address", activity.address)
        activity.thumbnail_url = request.POST.get("thumbnail_url", activity.thumbnail_url)
        activity.save()
        messages.success(request, f"'{activity.title}' 액티비티가 수정되었습니다.")
        return redirect("partner:activity_list")

    return render(request, "partner/activity_form.html", {
        "activity": activity,
        "categories": categories,
        "regions": regions,
        "editing": True,
    })


# ---------------------------------------------------------------------------
# 4. Slot Management
# ---------------------------------------------------------------------------

@partner_required
def slot_manage(request, pk):
    partner = _partner(request)
    activity = get_object_or_404(Activity, pk=pk, partner=partner)

    if request.method == "POST":
        action = request.POST.get("action")

        if action == "add":
            slot_date = request.POST.get("date")
            start_time = request.POST.get("start_time")
            capacity = int(request.POST.get("capacity", activity.capacity))
            if slot_date and start_time:
                slot, created = ActivitySlot.objects.get_or_create(
                    activity=activity,
                    date=slot_date,
                    start_time=start_time,
                    defaults={"remaining": capacity},
                )
                if created:
                    messages.success(request, f"{slot_date} {start_time} 슬롯이 추가되었습니다.")
                else:
                    messages.warning(request, "이미 동일한 슬롯이 존재합니다.")
            else:
                messages.error(request, "날짜와 시간을 모두 입력해주세요.")

        elif action == "delete":
            slot_id = request.POST.get("slot_id")
            deleted, _ = ActivitySlot.objects.filter(
                pk=slot_id, activity=activity
            ).delete()
            if deleted:
                messages.success(request, "슬롯이 삭제되었습니다.")
            else:
                messages.error(request, "슬롯을 찾을 수 없습니다.")

        return redirect("partner:slot_manage", pk=pk)

    slots = activity.slots.order_by("date", "start_time")

    # 날짜별로 그룹핑
    from collections import OrderedDict
    grouped = OrderedDict()
    for slot in slots:
        key = slot.date
        if key not in grouped:
            grouped[key] = []
        grouped[key].append(slot)

    return render(request, "partner/slot_manage.html", {
        "activity": activity,
        "grouped_slots": grouped,
    })


# ---------------------------------------------------------------------------
# 5. Booking Management
# ---------------------------------------------------------------------------

@partner_required
def booking_list(request):
    partner = _partner(request)
    status_filter = request.GET.get("status", "")

    bookings = Booking.objects.filter(
        slot__activity__partner=partner,
    ).select_related(
        "user", "slot__activity",
    ).order_by("-created_at")

    if status_filter and status_filter in dict(Booking.Status.choices):
        bookings = bookings.filter(status=status_filter)

    status_counts = dict(
        Booking.objects.filter(slot__activity__partner=partner)
        .values_list("status")
        .annotate(cnt=Count("id"))
        .values_list("status", "cnt")
    )
    total_count = sum(status_counts.values())

    return render(request, "partner/booking_list.html", {
        "bookings": bookings,
        "current_status": status_filter,
        "status_choices": Booking.Status.choices,
        "status_counts": status_counts,
        "total_count": total_count,
    })


# ---------------------------------------------------------------------------
# 5-1. Booking Complete (이용 완료 처리)
# ---------------------------------------------------------------------------

@partner_required
def booking_complete(request, pk):
    partner = _partner(request)
    booking = get_object_or_404(
        Booking.objects.select_related("slot__activity"),
        pk=pk,
        slot__activity__partner=partner,
    )
    if request.method == "POST" and booking.status == Booking.Status.CONFIRMED:
        booking.status = Booking.Status.COMPLETED
        booking.save(update_fields=["status", "updated_at"])
        messages.success(request, f"예약 {booking.reservation_code}이 이용 완료 처리되었습니다.")
    return redirect("partner:booking_list")


# ---------------------------------------------------------------------------
# 6. Settlement View
# ---------------------------------------------------------------------------

@partner_required
def settlement_list(request):
    partner = _partner(request)

    settlements = Settlement.objects.filter(
        partner=partner,
    ).order_by("-period_start")

    total_settlement = settlements.aggregate(total=Sum("settlement_amount"))["total"] or 0
    pending_amount = settlements.filter(
        status__in=[Settlement.Status.PENDING, Settlement.Status.PROCESSING],
    ).aggregate(total=Sum("settlement_amount"))["total"] or 0
    completed_amount = settlements.filter(
        status=Settlement.Status.COMPLETED,
    ).aggregate(total=Sum("settlement_amount"))["total"] or 0

    return render(request, "partner/settlement_list.html", {
        "settlements": settlements,
        "total_settlement": total_settlement,
        "pending_amount": pending_amount,
        "completed_amount": completed_amount,
    })
