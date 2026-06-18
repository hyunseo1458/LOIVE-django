from django.db import models
from django.conf import settings


class Category(models.Model):
    name = models.CharField("카테고리명", max_length=30, unique=True)
    slug = models.SlugField(unique=True)
    icon = models.CharField("아이콘 클래스", max_length=50, blank=True)
    order = models.PositiveSmallIntegerField("정렬 순서", default=0)

    class Meta:
        db_table = "categories"
        ordering = ["order"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Region(models.Model):
    name = models.CharField("지역명", max_length=30, unique=True)
    slug = models.SlugField(unique=True)

    class Meta:
        db_table = "regions"

    def __str__(self):
        return self.name


class Activity(models.Model):
    class Status(models.TextChoices):
        DRAFT = "draft", "임시저장"
        PENDING = "pending", "심사 대기"
        APPROVED = "approved", "승인"
        REJECTED = "rejected", "반려"

    partner = models.ForeignKey(
        "accounts.Partner", on_delete=models.CASCADE, related_name="activities"
    )
    category = models.ForeignKey(Category, on_delete=models.PROTECT, related_name="activities")
    region = models.ForeignKey(Region, on_delete=models.PROTECT, related_name="activities")
    title = models.CharField("제목", max_length=200)
    description = models.TextField("상세 설명")
    price = models.PositiveIntegerField("가격 (원)")
    capacity = models.PositiveSmallIntegerField("최대 정원")
    duration_minutes = models.PositiveSmallIntegerField("소요 시간 (분)", default=60)
    address = models.CharField("상세 주소", max_length=300, blank=True)
    latitude = models.DecimalField("위도", max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField("경도", max_digits=9, decimal_places=6, null=True, blank=True)
    thumbnail_url = models.URLField("썸네일 URL", max_length=500, blank=True, help_text="외부 이미지 URL (개발용)")
    status = models.CharField(max_length=10, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "activities"
        verbose_name_plural = "activities"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title

    @property
    def rating_avg(self):
        reviews = self.reviews.all()
        if not reviews.exists():
            return 0
        return round(reviews.aggregate(avg=models.Avg("rating"))["avg"], 1)


class ActivityImage(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="images")
    image = models.ImageField("이미지", upload_to="activities/%Y/%m/")
    is_primary = models.BooleanField("대표 이미지", default=False)
    order = models.PositiveSmallIntegerField("정렬 순서", default=0)

    class Meta:
        db_table = "activity_images"
        ordering = ["order"]


class ActivitySlot(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="slots")
    date = models.DateField("운영 날짜")
    start_time = models.TimeField("시작 시간")
    remaining = models.PositiveSmallIntegerField("잔여 정원")

    class Meta:
        db_table = "activity_slots"
        ordering = ["date", "start_time"]
        constraints = [
            models.UniqueConstraint(
                fields=["activity", "date", "start_time"],
                name="unique_activity_slot",
            )
        ]

    def __str__(self):
        return f"{self.activity.title} | {self.date} {self.start_time}"


class Course(models.Model):
    title = models.CharField("코스명", max_length=200)
    description = models.TextField("코스 설명")
    price = models.PositiveIntegerField("코스 가격 (원)")
    activities = models.ManyToManyField(Activity, related_name="courses")
    image = models.ImageField("대표 이미지", upload_to="courses/%Y/%m/", blank=True)
    is_active = models.BooleanField("노출 여부", default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "courses"
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Review(models.Model):
    activity = models.ForeignKey(Activity, on_delete=models.CASCADE, related_name="reviews")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    rating = models.PositiveSmallIntegerField("평점", choices=[(i, str(i)) for i in range(1, 6)])
    content = models.TextField("리뷰 내용")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "reviews"
        ordering = ["-created_at"]
        constraints = [
            models.UniqueConstraint(
                fields=["activity", "user"],
                name="unique_review_per_user",
            )
        ]

    def __str__(self):
        return f"{self.user} → {self.activity.title} ({self.rating}점)"
