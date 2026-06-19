from django.conf import settings
from django.db import models


class Wishlist(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="wishlists",
    )
    activity = models.ForeignKey(
        "activities.Activity",
        on_delete=models.CASCADE,
        related_name="wishlisted_by",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ("user", "activity")
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.user} → {self.activity}"
