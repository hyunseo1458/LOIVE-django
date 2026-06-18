from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = ["reservation_code", "user", "get_activity", "headcount", "total_amount", "status", "created_at"]
    list_filter = ["status"]
    search_fields = ["reservation_code", "user__username", "user__email"]
    readonly_fields = ["reservation_code", "created_at", "updated_at"]

    @admin.display(description="액티비티")
    def get_activity(self, obj):
        return obj.slot.activity.title
