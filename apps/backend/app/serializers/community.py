"""
Serializers for Community features (Feed, Like, Comment).
"""
from rest_framework import serializers
from app.models import Generation, Like, Comment, Follow, User, Style


class FeedUserSerializer(serializers.ModelSerializer):
    """Minimal user info for feed items."""

    class Meta:
        model = User
        fields = ["id", "username", "profile_image"]
        read_only_fields = fields


class FeedStyleSerializer(serializers.ModelSerializer):
    """Minimal style info for feed items."""

    artist_name = serializers.CharField(source="artist.username", read_only=True)

    class Meta:
        model = Style
        fields = ["id", "name", "artist_name"]
        read_only_fields = fields


class GenerationFeedSerializer(serializers.ModelSerializer):
    """Serializer for generation list in feed."""

    user = FeedUserSerializer(read_only=True)
    style = FeedStyleSerializer(read_only=True)
    is_liked_by_current_user = serializers.SerializerMethodField()

    class Meta:
        model = Generation
        fields = [
            "id",
            "user",
            "style",
            "result_url",
            "description",
            "like_count",
            "comment_count",
            "is_liked_by_current_user",
            "created_at",
        ]
        read_only_fields = fields

    def get_is_liked_by_current_user(self, obj):
        """Check if current user liked this generation."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, generation=obj).exists()
        return False


class GenerationDetailSerializer(serializers.ModelSerializer):
    """Serializer for generation detail view."""

    user = FeedUserSerializer(read_only=True)
    style = FeedStyleSerializer(read_only=True)
    is_liked_by_current_user = serializers.SerializerMethodField()

    class Meta:
        model = Generation
        fields = [
            "id",
            "user",
            "style",
            "result_url",
            "description",
            "aspect_ratio",
            "seed",
            "like_count",
            "comment_count",
            "is_liked_by_current_user",
            "created_at",
        ]
        read_only_fields = fields

    def get_is_liked_by_current_user(self, obj):
        """Check if current user liked this generation."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, generation=obj).exists()
        return False


class CommentUserSerializer(serializers.ModelSerializer):
    """User info for comments."""

    class Meta:
        model = User
        fields = ["id", "username", "profile_image"]
        read_only_fields = fields


class CommentSerializer(serializers.ModelSerializer):
    """Serializer for comments."""

    user = CommentUserSerializer(read_only=True)
    reply_count = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            "id",
            "user",
            "content",
            "like_count",
            "reply_count",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "like_count",
            "reply_count",
            "created_at",
            "updated_at",
        ]

    def get_reply_count(self, obj):
        """Get count of replies to this comment."""
        return obj.replies.count()

    def validate_content(self, value):
        """Validate comment content."""
        if not value or not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty.")
        if len(value) > 500:
            raise serializers.ValidationError(
                "Comment content must be 500 characters or less."
            )
        return value.strip()


class CommentCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating comments."""

    class Meta:
        model = Comment
        fields = ["content", "parent"]

    def validate_content(self, value):
        """Validate comment content."""
        if not value or not value.strip():
            raise serializers.ValidationError("Comment content cannot be empty.")
        if len(value) > 500:
            raise serializers.ValidationError(
                "Comment content must be 500 characters or less."
            )
        return value.strip()


class LikeToggleSerializer(serializers.Serializer):
    """Serializer for like toggle response."""

    is_liked = serializers.BooleanField()
    like_count = serializers.IntegerField()


class FollowToggleSerializer(serializers.Serializer):
    """Serializer for follow toggle response."""

    is_following = serializers.BooleanField()
    follower_count = serializers.IntegerField()


class FollowingUserSerializer(serializers.ModelSerializer):
    """Serializer for following list."""

    follower_count = serializers.IntegerField(source="followers.count", read_only=True)
    is_following = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "profile_image",
            "bio",
            "follower_count",
            "is_following",
        ]
        read_only_fields = fields

    def get_is_following(self, obj):
        """Always true in following list."""
        return True


class ArtistSerializer(serializers.Serializer):
    """Serializer for artist profile info within user profile."""

    id = serializers.IntegerField()
    artist_name = serializers.CharField(source="username")
    follower_count = serializers.IntegerField()


class UserStatsSerializer(serializers.Serializer):
    """Serializer for user statistics."""

    total_generations = serializers.IntegerField()
    public_generations = serializers.IntegerField()
    following_count = serializers.IntegerField()


class UserProfileSerializer(serializers.ModelSerializer):
    """
    Detailed user profile serializer.
    Used for GET /api/users/:id
    """

    artist = serializers.SerializerMethodField()
    stats = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
            "profile_image",
            "bio",
            "role",
            "created_at",
            "artist",
            "stats",
        ]
        read_only_fields = ["id", "email", "role", "created_at"]

    def get_artist(self, obj):
        """Return artist info if user is an artist."""
        if obj.role != "artist":
            return None

        from app.models import Follow, Artist

        follower_count = Follow.objects.filter(following=obj).count()

        # Get artist profile for signature
        artist_profile = None
        signature_image_url = None
        try:
            artist_profile = Artist.objects.get(user=obj)
            signature_image_url = artist_profile.signature_image_url
        except Artist.DoesNotExist:
            pass

        return {
            "id": obj.id,
            "artist_name": obj.username,
            "follower_count": follower_count,
            "signature_image_url": signature_image_url,
        }

    def get_stats(self, obj):
        """Return user statistics."""
        from app.models import Generation, Follow

        total_generations = Generation.objects.filter(user=obj).count()
        public_generations = Generation.objects.filter(
            user=obj, is_public=True, status="completed"
        ).count()
        following_count = Follow.objects.filter(follower=obj).count()

        return {
            "total_generations": total_generations,
            "public_generations": public_generations,
            "following_count": following_count,
        }


class UserUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating user profile.
    Used for PATCH /api/users/me
    Supports signature_image upload (stored in Artist profile if user is an artist)
    """

    signature_image = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["username", "bio", "profile_image", "signature_image"]

    def update(self, instance, validated_data):
        """Update user profile and handle signature_image for artists."""
        from app.models import Artist

        # Extract signature_image if provided
        signature_image = validated_data.pop("signature_image", None)

        # Update user fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # If signature_image provided, save to Artist profile
        if signature_image:
            # Get or create artist profile
            artist_profile, created = Artist.objects.get_or_create(user=instance)

            # Upload signature image to GCS using google-cloud-storage client
            from google.cloud import storage
            from django.conf import settings
            import logging

            logger = logging.getLogger(__name__)

            try:
                # Initialize GCS client
                storage_client = storage.Client()
                bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)

                # Generate filename
                filename = f"signatures/user_{instance.id}_{signature_image.name}"

                # Create blob and upload
                blob = bucket.blob(filename)
                blob.upload_from_file(signature_image, content_type=signature_image.content_type)

                # Make the blob publicly accessible
                blob.make_public()

                # Get public URL
                signature_url = blob.public_url

                logger.info(f"[Signature] Uploaded signature for user {instance.id}: {signature_url}")

                # Update artist profile
                artist_profile.signature_image_url = signature_url
                artist_profile.save()

            except Exception as e:
                logger.error(f"[Signature] Failed to upload signature for user {instance.id}: {e}", exc_info=True)
                raise serializers.ValidationError(f"Failed to upload signature: {str(e)}")

        return instance
