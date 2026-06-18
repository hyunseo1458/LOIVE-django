from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [
    path("", views.booking_history, name="history"),
    path("detail/<int:pk>/", views.booking_detail, name="detail"),
    path("detail/<int:pk>/cancel/", views.booking_cancel, name="cancel"),
    path("<int:activity_id>/", views.booking_form, name="form"),
    path("<int:activity_id>/complete/", views.booking_complete, name="complete"),
]
