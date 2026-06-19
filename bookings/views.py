import uuid
import calendar
from datetime import date, timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.db.models import F
from activities.models import Activity, ActivitySlot
from .models import Booking


@login_required
def booking_history(request):

    bookings = Booking.objects.filter(
        user=request.user
    ).select_related("slot__activity").order_by("-created_at")

    upcoming = bookings.filter(status=Booking.Status.CONFIRMED)
    completed = bookings.filter(status=Booking.Status.COMPLETED)
    cancelled = bookings.filter(status__in=[Booking.Status.CANCELLED, Booking.Status.REFUNDED])

    return render(request, "bookings/history.html", {
        "upcoming": upcoming,
        "completed": completed,
        "cancelled": cancelled,
    })


@login_required
def booking_form(request, activity_id):
    activity = get_object_or_404(Activity, pk=activity_id, status=Activity.Status.APPROVED)
    slots = activity.slots.filter(remaining__gt=0).order_by("date", "start_time")

    slot_dates = sorted(slots.values_list("date", flat=True).distinct())

    if slot_dates:
        first_date = slot_dates[0]
    else:
        first_date = date.today()

    cal_year = first_date.year
    cal_month = first_date.month
    _, last_day = calendar.monthrange(cal_year, cal_month)
    cal_start = date(cal_year, cal_month, 1)
    cal_end = date(cal_year, cal_month, last_day)

    cal_weeks = calendar.monthcalendar(cal_year, cal_month)
    available_set = {d.isoformat() for d in slot_dates if d.month == cal_month and d.year == cal_year}

    cal_data = []
    for week in cal_weeks:
        row = []
        for day_num in week:
            if day_num == 0:
                row.append({"day": 0, "iso": "", "available": False})
            else:
                d = date(cal_year, cal_month, day_num)
                row.append({
                    "day": day_num,
                    "iso": d.isoformat(),
                    "available": d.isoformat() in available_set,
                })
        cal_data.append(row)

    if request.method == "POST":
        slot_id = request.POST.get("slot_id")
        try:
            adults = max(1, int(request.POST.get("adults", 1)))
            children = max(0, int(request.POST.get("children", 0)))
        except (ValueError, TypeError):
            adults, children = 1, 0
        headcount = adults + children
        special_request = request.POST.get("special_request", "")

        with transaction.atomic():
            slot = ActivitySlot.objects.select_for_update().get(pk=slot_id, activity=activity)
            already_booked = Booking.objects.filter(
                user=request.user, slot=slot, status=Booking.Status.CONFIRMED,
            ).exists()
            if not already_booked and headcount <= slot.remaining and headcount <= activity.capacity:
                slot.remaining = F("remaining") - headcount
                slot.save(update_fields=["remaining"])

                reservation_code = f"LV-{uuid.uuid4().hex[:8].upper()}"
                booking = Booking.objects.create(
                    user=request.user,
                    slot=slot,
                    headcount=headcount,
                    total_amount=activity.price * adults,
                    status=Booking.Status.CONFIRMED,
                    reservation_code=reservation_code,
                    special_request=special_request,
                )
                return redirect("bookings:complete", activity_id=activity_id)

    return render(request, "bookings/form.html", {
        "activity": activity,
        "slots": slots,
        "cal_year": cal_year,
        "cal_month": cal_month,
        "cal_data": cal_data,
        "available_dates": available_set,
        "weekdays": ["일", "월", "화", "수", "목", "금", "토"],
    })


def booking_complete(request, activity_id):
    activity = get_object_or_404(Activity, pk=activity_id)
    booking = None
    if request.user.is_authenticated:
        booking = Booking.objects.filter(
            user=request.user, slot__activity=activity
        ).select_related("slot__activity").order_by("-created_at").first()

    return render(request, "bookings/complete.html", {
        "activity": activity,
        "booking": booking,
    })


@login_required
def booking_detail(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related("slot__activity__category", "slot__activity__region"),
        pk=pk, user=request.user,
    )
    return render(request, "bookings/detail.html", {
        "booking": booking,
    })


@login_required
def booking_cancel(request, pk):
    booking = get_object_or_404(
        Booking.objects.select_related("slot__activity__category", "slot__activity__region"),
        pk=pk, user=request.user,
    )

    if request.method == "POST" and booking.status == Booking.Status.CONFIRMED:
        reason = request.POST.get("reason", "")
        with transaction.atomic():
            booking.status = Booking.Status.CANCELLED
            booking.save(update_fields=["status", "updated_at"])
            slot = ActivitySlot.objects.select_for_update().get(pk=booking.slot_id)
            slot.remaining = F("remaining") + booking.headcount
            slot.save(update_fields=["remaining"])

        from django.contrib import messages
        messages.success(request, "예약이 성공적으로 취소되었습니다.")
        return redirect("bookings:detail", pk=pk)

    return render(request, "bookings/cancel.html", {
        "booking": booking,
    })
