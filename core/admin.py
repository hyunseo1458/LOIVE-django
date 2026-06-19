from django.contrib import admin
from core.models import Wishlist


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ("user", "activity", "created_at")
    list_filter = ("created_at",)
    raw_id_fields = ("user", "activity")
