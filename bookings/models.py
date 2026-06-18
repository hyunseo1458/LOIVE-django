from django.db import models
from django.conf import settings


class Booking(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "결제 대기"
        CONFIRMED = "confirmed", "결제 완료"
        COMPLETED = "completed", "이용 완료"
        CANCELLED = "cancelled", "취소"
        REFUNDED = "refunded", "환불 완료"

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    slot = models.ForeignKey("activities.ActivitySlot", on_delete=models.PROTECT, related_name="bookings")
    course = models.ForeignKey(
        "activities.Course", on_delete=models.SET_NULL, null=True, blank=True, related_name="bookings"
    )
    headcount = models.PositiveSmallIntegerField("예약 인원")
    total_amount = models.PositiveIntegerField("결제 금액")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    special_request = models.TextField("특별 요청사항", blank=True)
    reservation_code = models.CharField("예약번호", max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "bookings"
        ordering = ["-created_at"]

    def __str__(self):
        return f"[{self.reservation_code}] {self.user} - {self.slot.activity.title}"
