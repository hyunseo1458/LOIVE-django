from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    class Role(models.TextChoices):
        CUSTOMER = "customer", "일반 이용자"
        PARTNER = "partner", "파트너"
        ADMIN = "admin", "운영자"

    role = models.CharField(max_length=10, choices=Role.choices, default=Role.CUSTOMER)
    phone = models.CharField("연락처", max_length=20, blank=True)

    class Meta:
        db_table = "users"

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_role_display()})"

    @property
    def is_partner(self):
        return self.role == self.Role.PARTNER

    @property
    def is_admin_user(self):
        return self.role == self.Role.ADMIN


class Partner(models.Model):
    class Status(models.TextChoices):
        PENDING = "pending", "심사 대기"
        APPROVED = "approved", "승인"
        REJECTED = "rejected", "반려"

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="partner_profile")
    business_name = models.CharField("사업자명", max_length=100)
    business_number = models.CharField("사업자등록번호", max_length=12)
    bank_name = models.CharField("은행명", max_length=20)
    account_number = models.CharField("정산 계좌번호", max_length=30)
    account_holder = models.CharField("예금주", max_length=30)
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "partners"

    def __str__(self):
        return f"{self.business_name} ({self.get_status_display()})"
