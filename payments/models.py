from django.db import models


class Payment(models.Model):
    class Status(models.TextChoices):
        READY = "ready", "결제 준비"
        DONE = "done", "결제 완료"
        CANCELLED = "cancelled", "결제 취소"
        FAILED = "failed", "결제 실패"

    class Method(models.TextChoices):
        CARD = "card", "신용카드"
        KAKAOPAY = "kakaopay", "카카오페이"
        TOSSPAY = "tosspay", "토스페이"
        NAVERPAY = "naverpay", "네이버페이"

    booking = models.OneToOneField("bookings.Booking", on_delete=models.PROTECT, related_name="payment")
    order_id = models.CharField("주문번호", max_length=64, unique=True)
    payment_key = models.CharField("PG 결제키", max_length=200, blank=True)
    method = models.CharField(max_length=10, choices=Method.choices)
    amount = models.PositiveIntegerField("결제 금액")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.READY)
    pg_response = models.JSONField("PG 응답 원본", default=dict, blank=True)
    paid_at = models.DateTimeField("결제 시각", null=True, blank=True)
    cancelled_at = models.DateTimeField("취소 시각", null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "payments"

    def __str__(self):
        return f"[{self.order_id}] {self.get_status_display()} - {self.amount:,}원"


class WebhookLog(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name="webhook_logs")
    event_type = models.CharField("이벤트 유형", max_length=50)
    payload = models.JSONField("수신 데이터")
    processed = models.BooleanField("처리 완료", default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "webhook_logs"
        ordering = ["-created_at"]
