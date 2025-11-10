from django.db import models
from django.utils import timezone


class Tag(models.Model):
    """Tag model for categorizing styles, artworks, and generations."""

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Tag details
    name = models.CharField(max_length=100, unique=True)
    usage_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "tags"
        indexes = [
            models.Index(
                fields=["name"],
                name="idx_tags_name",
                condition=models.Q(is_active=True),
            ),
            models.Index(fields=["is_active", "-usage_count"], name="idx_tags_active"),
        ]

    def __str__(self):
        return f"{self.name} ({self.usage_count} uses)"

    def save(self, *args, **kwargs):
        """Override save to lowercase tag name."""
        self.name = self.name.lower()
        super().save(*args, **kwargs)


class StyleTag(models.Model):
    """M:N relationship between Style and Tag."""

    # Foreign keys (composite primary key)
    style = models.ForeignKey(
        "app.Style", on_delete=models.CASCADE, related_name="style_tags"
    )
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="style_tags")

    # Sequence for ordering tags
    sequence = models.IntegerField()

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "style_tags"
        constraints = [
            models.UniqueConstraint(fields=["style", "tag"], name="unique_style_tag"),
            models.UniqueConstraint(
                fields=["style", "sequence"], name="unique_style_sequence"
            ),
        ]
        indexes = [
            models.Index(fields=["tag"], name="idx_style_tags_tag"),
        ]

    def __str__(self):
        return f"{self.style.name} - {self.tag.name}"


class ArtworkTag(models.Model):
    """M:N relationship between Artwork and Tag."""

    # Foreign keys (composite primary key)
    artwork = models.ForeignKey(
        "app.Artwork", on_delete=models.CASCADE, related_name="artwork_tags"
    )
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name="artwork_tags")

    # Sequence for ordering tags
    sequence = models.IntegerField()

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "artwork_tags"
        constraints = [
            models.UniqueConstraint(
                fields=["artwork", "tag"], name="unique_artwork_tag"
            ),
            models.UniqueConstraint(
                fields=["artwork", "sequence"], name="unique_artwork_sequence"
            ),
        ]
        indexes = [
            models.Index(fields=["tag"], name="idx_artwork_tags_tag"),
        ]

    def __str__(self):
        return f"Artwork {self.artwork.id} - {self.tag.name}"


class GenerationTag(models.Model):
    """M:N relationship between Generation and Tag."""

    # Foreign keys (composite primary key)
    generation = models.ForeignKey(
        "app.Generation", on_delete=models.CASCADE, related_name="generation_tags"
    )
    tag = models.ForeignKey(
        Tag, on_delete=models.CASCADE, related_name="generation_tags"
    )

    # Sequence for ordering tags
    sequence = models.IntegerField()

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "generation_tags"
        constraints = [
            models.UniqueConstraint(
                fields=["generation", "tag"], name="unique_generation_tag"
            ),
            models.UniqueConstraint(
                fields=["generation", "sequence"], name="unique_generation_sequence"
            ),
        ]
        indexes = [
            models.Index(fields=["tag"], name="idx_generation_tags_tag"),
        ]

    def __str__(self):
        return f"Generation {self.generation.id} - {self.tag.name}"
