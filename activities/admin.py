from django.contrib import admin
from .models import Category, Region, Activity, ActivityImage, ActivitySlot, Course, Review


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "order"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


class ActivityImageInline(admin.TabularInline):
    model = ActivityImage
    extra = 1


class ActivitySlotInline(admin.TabularInline):
    model = ActivitySlot
    extra = 3


@admin.register(Activity)
class ActivityAdmin(admin.ModelAdmin):
    list_display = ["title", "partner", "category", "region", "price", "status", "created_at"]
    list_filter = ["status", "category", "region"]
    search_fields = ["title", "description"]
    inlines = [ActivityImageInline, ActivitySlotInline]
    actions = ["approve_activities", "reject_activities"]

    @admin.action(description="선택한 액티비티 승인")
    def approve_activities(self, request, queryset):
        queryset.update(status=Activity.Status.APPROVED)

    @admin.action(description="선택한 액티비티 반려")
    def reject_activities(self, request, queryset):
        queryset.update(status=Activity.Status.REJECTED)


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = ["title", "price", "is_active", "created_at"]
    filter_horizontal = ["activities"]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ["user", "activity", "rating", "created_at"]
    list_filter = ["rating"]
