from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("api/wishlist/", views.wishlist_api, name="wishlist_api"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("notifications/", views.notifications, name="notifications"),
    path("faq/", views.faq, name="faq"),
    path("terms/", views.terms, name="terms"),
    path("privacy/", views.privacy, name="privacy"),
]
