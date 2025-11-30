from django.db import models
from django.utils import timezone
from datetime import date


class Style(models.Model):
    """Style model representing an artist's trained AI style."""

    TRAINING_STATUS_CHOICES = [
        ("pending", "Pending"),
        ("training", "Training"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    LICENSE_TYPE_CHOICES = [
        ("personal", "Personal"),
        ("commercial", "Commercial"),
        ("exclusive", "Exclusive"),
    ]

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Foreign key
    artist = models.ForeignKey(
        "app.User", on_delete=models.CASCADE, related_name="styles"
    )

    # Basic fields
    name = models.CharField(max_length=100)
    description = models.TextField(null=True, blank=True)
    thumbnail_url = models.TextField(null=True, blank=True)

    # Model storage
    model_path = models.TextField(null=True, blank=True)

    # Training details
    training_status = models.CharField(
        max_length=20, choices=TRAINING_STATUS_CHOICES, default="pending"
    )
    training_log_path = models.TextField(null=True, blank=True)
    training_metric = models.JSONField(null=True, blank=True)
    training_progress = models.JSONField(null=True, blank=True)

    # License
    license_type = models.CharField(
        max_length=30, choices=LICENSE_TYPE_CHOICES, default="personal"
    )
    valid_from = models.DateField(default=date.today)
    valid_to = models.DateField(null=True, blank=True)

    # Pricing
    generation_cost_tokens = models.BigIntegerField(default=0)

    # Statistics (cached)
    usage_count = models.IntegerField(default=0)

    # Status flags
    is_flagged = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "styles"
        constraints = [
            models.UniqueConstraint(
                fields=["artist", "name"], name="unique_artist_style_name"
            ),
            models.CheckConstraint(
                check=models.Q(generation_cost_tokens__gte=0),
                name="generation_cost_tokens_non_negative",
            ),
            models.CheckConstraint(
                check=models.Q(
                    training_status__in=["pending", "training", "completed", "failed"]
                ),
                name="valid_training_status",
            ),
            models.CheckConstraint(
                check=models.Q(
                    license_type__in=["personal", "commercial", "exclusive"]
                ),
                name="valid_license_type",
            ),
        ]
        indexes = [
            models.Index(fields=["artist", "is_active"], name="idx_styles_artist"),
            models.Index(fields=["training_status"], name="idx_styles_status"),
            models.Index(
                fields=["is_active", "-created_at"],
                name="idx_styles_active",
                condition=models.Q(is_active=True),
            ),
            models.Index(
                fields=["-usage_count", "-created_at"], name="idx_styles_usage"
            ),
        ]

    def __str__(self):
        return f"{self.name} by {self.artist.username} ({self.training_status})"

    def save(self, *args, **kwargs):
        """Override save to ensure updated_at is set."""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)

    def is_ready(self):
        """Check if style is ready for generation."""
        return self.training_status == "completed" and self.model_path


class Artwork(models.Model):
    """Artwork model for training images."""

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Foreign key
    style = models.ForeignKey(Style, on_delete=models.CASCADE, related_name="artworks")

    # Image URLs
    image_url = models.TextField()
    processed_image_url = models.TextField(null=True, blank=True)

    # Caption for Stable Diffusion Fine-tuning
    caption = models.TextField(null=True, blank=True)

    # Validation
    is_valid = models.BooleanField(default=True)
    validation_reason = models.TextField(null=True, blank=True)

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "artworks"
        indexes = [
            models.Index(fields=["style"], name="idx_artworks_style"),
            models.Index(
                fields=["is_valid"],
                name="idx_artworks_valid",
                condition=models.Q(is_valid=True),
            ),
        ]

    def __str__(self):
        return f"Artwork {self.id} for {self.style.name}"
