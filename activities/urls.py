from django.urls import path
from . import views

app_name = "activities"

urlpatterns = [
    path("", views.explore, name="explore"),
    path("course/<int:pk>/", views.course_detail, name="course_detail"),
    path("<int:pk>/", views.detail, name="detail"),
    path("<int:pk>/reviews/", views.reviews, name="reviews"),
    path("<int:pk>/review/", views.write_review, name="write_review"),
]
