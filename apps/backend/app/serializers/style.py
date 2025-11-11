"""
Style Serializers for Style Model API.

Provides different serializers for different use cases:
- StyleListSerializer: For list view (minimal fields)
- StyleDetailSerializer: For detail view (all fields + nested data)
- StyleCreateSerializer: For creating new styles (with validation)
"""
from rest_framework import serializers
from app.models import Style, Artwork, Tag, StyleTag
from app.serializers.base import BaseSerializer


class ArtworkSerializer(serializers.ModelSerializer):
    """Serializer for Artwork model (training images)."""

    class Meta:
        model = Artwork
        fields = ["id", "image_url", "is_valid", "created_at"]
        read_only_fields = ["id", "is_valid", "created_at"]


class TagSerializer(serializers.ModelSerializer):
    """Serializer for Tag model."""

    class Meta:
        model = Tag
        fields = ["id", "name", "usage_count"]
        read_only_fields = ["id", "usage_count"]


class StyleListSerializer(BaseSerializer):
    """
    Serializer for Style list view.

    Includes minimal fields for performance:
    - id, name, artist info, thumbnail, price, usage_count
    """

    artist_username = serializers.CharField(source="artist.username", read_only=True)
    artist_id = serializers.IntegerField(source="artist.id", read_only=True)
    tags = serializers.SerializerMethodField()

    class Meta:
        model = Style
        fields = [
            "id",
            "name",
            "artist_id",
            "artist_username",
            "thumbnail_url",
            "generation_cost_tokens",
            "usage_count",
            "training_status",
            "tags",
            "created_at",
        ]
        read_only_fields = fields

    def get_tags(self, obj):
        """Get tag names associated with this style."""
        # Get tags through StyleTag relationship, ordered by sequence
        style_tags = obj.style_tags.select_related("tag").order_by("sequence")
        return [st.tag.name for st in style_tags]


class StyleDetailSerializer(BaseSerializer):
    """
    Serializer for Style detail view.

    Includes all fields plus nested data:
    - Full style information
    - Artist details
    - Training images (artworks)
    - Tags
    """

    artist_username = serializers.CharField(source="artist.username", read_only=True)
    artist_id = serializers.IntegerField(source="artist.id", read_only=True)
    artist_profile_image = serializers.CharField(
        source="artist.profile_image", read_only=True
    )

    # Nested serializers
    artworks = ArtworkSerializer(many=True, read_only=True)
    tags = serializers.SerializerMethodField()

    # Computed fields
    is_ready = serializers.SerializerMethodField()

    class Meta:
        model = Style
        fields = [
            "id",
            "name",
            "description",
            "artist_id",
            "artist_username",
            "artist_profile_image",
            "thumbnail_url",
            "model_path",
            "training_status",
            "training_log_path",
            "training_metric",
            "training_progress",
            "license_type",
            "valid_from",
            "valid_to",
            "generation_cost_tokens",
            "usage_count",
            "is_flagged",
            "is_active",
            "artworks",
            "tags",
            "is_ready",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "model_path",
            "training_status",
            "training_log_path",
            "training_metric",
            "training_progress",
            "usage_count",
            "is_flagged",
            "created_at",
            "updated_at",
        ]

    def get_tags(self, obj):
        """Get tags with full details."""
        style_tags = obj.style_tags.select_related("tag").order_by("sequence")
        return [
            {"id": st.tag.id, "name": st.tag.name, "sequence": st.sequence}
            for st in style_tags
        ]

    def get_is_ready(self, obj):
        """Check if style is ready for generation."""
        return obj.is_ready()


class StyleCreateSerializer(serializers.ModelSerializer):
    """
    Serializer for creating new Style with training images.

    Validates:
    - 10-100 training images required
    - JPG/PNG only
    - Max 10MB per image
    - Tags assignment
    """

    # Write-only fields for image upload
    training_images = serializers.ListField(
        child=serializers.ImageField(max_length=None, use_url=False),
        write_only=True,
        required=True,
        help_text="List of training images (10-100 images, JPG/PNG, max 10MB each)",
    )

    # Tags: accept list of tag names
    tags = serializers.ListField(
        child=serializers.CharField(max_length=100),
        write_only=True,
        required=False,
        allow_empty=True,
        help_text="List of tag names (e.g. ['watercolor', 'portrait'])",
    )

    # Read-only fields
    artist_username = serializers.CharField(source="artist.username", read_only=True)

    class Meta:
        model = Style
        fields = [
            "id",
            "name",
            "description",
            "artist_username",
            "license_type",
            "valid_from",
            "valid_to",
            "generation_cost_tokens",
            "training_images",
            "tags",
            "training_status",
            "created_at",
        ]
        read_only_fields = ["id", "artist_username", "training_status", "created_at"]

    def validate_name(self, value):
        """Validate style name."""
        if len(value) < 3:
            raise serializers.ValidationError("Style name must be at least 3 characters")
        if len(value) > 100:
            raise serializers.ValidationError(
                "Style name cannot exceed 100 characters"
            )
        return value

    def validate_generation_cost_tokens(self, value):
        """Validate generation cost."""
        if value < 0:
            raise serializers.ValidationError("Generation cost cannot be negative")
        if value > 10000:
            raise serializers.ValidationError(
                "Generation cost cannot exceed 10,000 tokens"
            )
        return value

    def validate_training_images(self, value):
        """Validate training images count and format."""
        # Check count
        if len(value) < 10:
            raise serializers.ValidationError(
                f"At least 10 training images required. Got {len(value)}"
            )
        if len(value) > 100:
            raise serializers.ValidationError(
                f"Maximum 100 training images allowed. Got {len(value)}"
            )

        # Check file format and size
        allowed_formats = ["image/jpeg", "image/png", "image/jpg"]
        max_size_mb = 10
        max_size_bytes = max_size_mb * 1024 * 1024

        for idx, image in enumerate(value):
            # Check format
            if image.content_type not in allowed_formats:
                raise serializers.ValidationError(
                    f"Image {idx + 1}: Invalid format '{image.content_type}'. "
                    f"Only JPG/PNG allowed."
                )

            # Check size
            if image.size > max_size_bytes:
                size_mb = image.size / (1024 * 1024)
                raise serializers.ValidationError(
                    f"Image {idx + 1}: File size {size_mb:.2f}MB exceeds "
                    f"maximum {max_size_mb}MB"
                )

        return value

    def validate_tags(self, value):
        """Validate tags."""
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 tags allowed")

        # Normalize tag names
        normalized_tags = []
        for tag_name in value:
            # Remove extra spaces and lowercase
            normalized = tag_name.strip().lower()
            if not normalized:
                continue
            if len(normalized) > 100:
                raise serializers.ValidationError(
                    f"Tag '{tag_name}' exceeds 100 characters"
                )
            normalized_tags.append(normalized)

        # Remove duplicates while preserving order
        seen = set()
        unique_tags = []
        for tag in normalized_tags:
            if tag not in seen:
                seen.add(tag)
                unique_tags.append(tag)

        return unique_tags

    def validate(self, attrs):
        """Cross-field validation."""
        # Check artist uniqueness (artist + name must be unique)
        request = self.context.get("request")
        if request and hasattr(request, "user"):
            artist = request.user
            name = attrs.get("name")
            if Style.objects.filter(artist=artist, name=name).exists():
                raise serializers.ValidationError(
                    {"name": f"You already have a style named '{name}'"}
                )

        return attrs

    def create(self, validated_data):
        """Create Style with artworks and tags."""
        # Extract nested data
        training_images = validated_data.pop("training_images", [])
        tag_names = validated_data.pop("tags", [])

        # Create Style instance
        # Note: artist will be set in ViewSet's perform_create()
        style = Style.objects.create(**validated_data)

        # Create Artwork instances (image upload will be handled in ViewSet)
        # For now, we just create placeholder Artwork records
        # The actual image upload to S3 will be done in the ViewSet
        for image in training_images:
            Artwork.objects.create(
                style=style, image_url="", is_valid=False  # Placeholder
            )

        # Create or get tags and associate with style
        for idx, tag_name in enumerate(tag_names):
            tag, _ = Tag.objects.get_or_create(name=tag_name)
            StyleTag.objects.create(style=style, tag=tag, sequence=idx)
            # Increment usage count
            tag.usage_count += 1
            tag.save(update_fields=["usage_count"])

        return style
