from django.contrib import admin
from .models import Payment, WebhookLog


class WebhookLogInline(admin.TabularInline):
    model = WebhookLog
    extra = 0
    readonly_fields = ["event_type", "payload", "processed", "created_at"]


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ["order_id", "booking", "method", "amount", "status", "paid_at"]
    list_filter = ["status", "method"]
    search_fields = ["order_id", "payment_key"]
    readonly_fields = ["pg_response"]
    inlines = [WebhookLogInline]


@admin.register(WebhookLog)
class WebhookLogAdmin(admin.ModelAdmin):
    list_display = ["payment", "event_type", "processed", "created_at"]
    list_filter = ["processed", "event_type"]
