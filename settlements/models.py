from django.db import models


class Settlement(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "정산 예정"
        PROCESSING = "processing", "처리 중"
        COMPLETED = "completed", "정산 완료"
        FAILED = "failed", "정산 실패"

    partner = models.ForeignKey("accounts.Partner", on_delete=models.PROTECT, related_name="settlements")
    bookings = models.ManyToManyField("bookings.Booking", related_name="settlements")
    total_sales = models.PositiveIntegerField("총 매출액")
    platform_fee = models.PositiveIntegerField("플랫폼 수수료")
    settlement_amount = models.PositiveIntegerField("정산 금액")
    status = models.CharField(max_length=12, choices=Status.choices, default=Status.PENDING)
    period_start = models.DateField("정산 시작일")
    period_end = models.DateField("정산 종료일")
    settled_at = models.DateTimeField("정산 완료일", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "settlements"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.partner} | {self.period_start}~{self.period_end} | {self.settlement_amount:,}원"
