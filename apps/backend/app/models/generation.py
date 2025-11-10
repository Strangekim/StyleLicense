from django.db import models
from django.utils import timezone


class Generation(models.Model):
    """Generation model for AI-generated images."""

    STATUS_CHOICES = [
        ("queued", "Queued"),
        ("processing", "Processing"),
        ("retrying", "Retrying"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    ASPECT_RATIO_CHOICES = [
        ("1:1", "1:1"),
        ("2:2", "2:2"),
        ("1:2", "1:2"),
    ]

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Foreign keys
    user = models.ForeignKey(
        "app.User", on_delete=models.CASCADE, related_name="generations"
    )
    style = models.ForeignKey(
        "app.Style", on_delete=models.RESTRICT, related_name="generations"
    )

    # Generation parameters
    aspect_ratio = models.CharField(
        max_length=10, choices=ASPECT_RATIO_CHOICES, default="1:1"
    )
    seed = models.BigIntegerField(null=True, blank=True)

    # Token cost
    consumed_tokens = models.BigIntegerField(default=0)

    # Result
    result_url = models.TextField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="queued")
    generation_progress = models.JSONField(null=True, blank=True)

    # Content
    description = models.TextField(null=True, blank=True)

    # Statistics (cached)
    like_count = models.IntegerField(default=0)
    comment_count = models.IntegerField(default=0)

    # Privacy
    is_public = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "generations"
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    status__in=[
                        "queued",
                        "processing",
                        "retrying",
                        "completed",
                        "failed",
                    ]
                ),
                name="valid_generation_status",
            ),
        ]
        indexes = [
            models.Index(fields=["user", "-created_at"], name="idx_generations_user"),
            models.Index(fields=["style", "status"], name="idx_generations_style"),
            models.Index(fields=["status"], name="idx_generations_status"),
            models.Index(
                fields=["is_public", "-created_at"],
                name="idx_generations_public",
                condition=models.Q(is_public=True),
            ),
        ]

    def __str__(self):
        return f"Generation {self.id} by {self.user.username} ({self.status})"

    def save(self, *args, **kwargs):
        """Override save to ensure updated_at is set."""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
