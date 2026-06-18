from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Partner


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ["username", "email", "role", "is_active", "date_joined"]
    list_filter = ["role", "is_active"]
    fieldsets = BaseUserAdmin.fieldsets + (
        ("로이브", {"fields": ("role", "phone")}),
    )


@admin.register(Partner)
class PartnerAdmin(admin.ModelAdmin):
    list_display = ["business_name", "user", "business_number", "status", "created_at"]
    list_filter = ["status"]
    actions = ["approve_partners", "reject_partners"]

    @admin.action(description="선택한 파트너 승인")
    def approve_partners(self, request, queryset):
        from django.utils import timezone
        queryset.update(status=Partner.Status.APPROVED, approved_at=timezone.now())
        for partner in queryset:
            partner.user.role = User.Role.PARTNER
            partner.user.save(update_fields=["role"])

    @admin.action(description="선택한 파트너 반려")
    def reject_partners(self, request, queryset):
        queryset.update(status=Partner.Status.REJECTED)
