from django.urls import path
from . import partner_views

app_name = "partner"

urlpatterns = [
    path("", partner_views.dashboard, name="dashboard"),
    path("activities/", partner_views.activity_list, name="activity_list"),
    path("activities/new/", partner_views.activity_create, name="activity_create"),
    path("activities/<int:pk>/edit/", partner_views.activity_edit, name="activity_edit"),
    path("activities/<int:pk>/slots/", partner_views.slot_manage, name="slot_manage"),
    path("bookings/", partner_views.booking_list, name="booking_list"),
    path("bookings/<int:pk>/complete/", partner_views.booking_complete, name="booking_complete"),
    path("settlements/", partner_views.settlement_list, name="settlement_list"),
]
