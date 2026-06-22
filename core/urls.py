from django.urls import path
from . import views

app_name = "core"

urlpatterns = [
    path("", views.home, name="home"),
    path("search/", views.search, name="search"),
    path("wishlist/", views.wishlist, name="wishlist"),
    path("api/wishlist/toggle/", views.wishlist_toggle, name="wishlist_toggle"),
    path("api/wishlist/ids/", views.wishlist_ids, name="wishlist_ids"),
    path("profile/", views.profile, name="profile"),
    path("profile/edit/", views.profile_edit, name="profile_edit"),
    path("profile/reviews/", views.my_reviews, name="my_reviews"),
    path("notifications/", views.notifications, name="notifications"),
    path("faq/", views.faq, name="faq"),
    path("terms/", views.terms, name="terms"),
    path("privacy/", views.privacy, name="privacy"),
    path("api/set-lang/", views.set_lang, name="set_lang"),
]
