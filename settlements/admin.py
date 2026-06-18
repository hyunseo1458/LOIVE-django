from django.contrib import admin
from .models import Settlement


@admin.register(Settlement)
class SettlementAdmin(admin.ModelAdmin):
    list_display = ["partner", "period_start", "period_end", "total_sales", "platform_fee", "settlement_amount", "status"]
    list_filter = ["status"]
    filter_horizontal = ["bookings"]
