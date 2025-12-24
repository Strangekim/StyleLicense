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

    artist = serializers.SerializerMethodField()

    class Meta:
        model = Style
        fields = ["id", "name", "artist"]
        read_only_fields = ["id", "name"]

    def get_artist(self, obj):
        """Return artist info."""
        if obj.artist:
            return {
                "id": obj.artist.id,
                "artist_name": obj.artist.username,
                "profile_image": obj.artist.profile_image,
            }
        return None


class GenerationFeedSerializer(serializers.ModelSerializer):
    """Serializer for generation list in feed."""

    user = FeedUserSerializer(read_only=True)
    style = FeedStyleSerializer(read_only=True)
    is_liked_by_current_user = serializers.SerializerMethodField()
    result_url = serializers.SerializerMethodField()

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

    def get_result_url(self, obj):
        """Convert GCS URI to HTTPS URL for browser compatibility."""
        result_url = obj.result_url
        if result_url and result_url.startswith("gs://"):
            return result_url.replace("gs://", "https://storage.googleapis.com/", 1)
        return result_url


class GenerationDetailSerializer(serializers.ModelSerializer):
    """Serializer for generation detail view."""

    user = FeedUserSerializer(read_only=True)
    style = FeedStyleSerializer(read_only=True)
    is_liked_by_current_user = serializers.SerializerMethodField()
    tags = serializers.SerializerMethodField()
    result_url = serializers.SerializerMethodField()

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
            "is_public",
            "tags",
            "created_at",
        ]
        read_only_fields = fields

    def get_is_liked_by_current_user(self, obj):
        """Check if current user liked this generation."""
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Like.objects.filter(user=request.user, generation=obj).exists()
        return False

    def get_tags(self, obj):
        """Get prompt tags from generation_progress."""
        if obj.generation_progress and isinstance(obj.generation_progress, dict):
            return obj.generation_progress.get("prompt_tags", [])
        return []

    def get_result_url(self, obj):
        """Convert GCS URI to HTTPS URL for browser compatibility."""
        result_url = obj.result_url
        if result_url and result_url.startswith("gs://"):
            return result_url.replace("gs://", "https://storage.googleapis.com/", 1)
        return result_url


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

    profile_image = serializers.ImageField(write_only=True, required=False)
    signature_image = serializers.ImageField(write_only=True, required=False)

    class Meta:
        model = User
        fields = ["username", "bio", "profile_image", "signature_image"]

    def update(self, instance, validated_data):
        """Update user profile and handle profile_image and signature_image uploads."""
        from app.models import Artist
        from google.cloud import storage
        from django.conf import settings
        import logging
        from urllib.parse import urlparse

        logger = logging.getLogger(__name__)

        # Extract image files if provided
        profile_image = validated_data.pop("profile_image", None)
        signature_image = validated_data.pop("signature_image", None)

        # Update user fields (text fields only)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # Upload profile_image to GCS if provided
        if profile_image:
            try:
                # Initialize GCS client
                storage_client = storage.Client()
                bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)

                # Delete old profile image if exists
                old_profile_image = instance.profile_image
                if old_profile_image:
                    try:
                        parsed_url = urlparse(old_profile_image)
                        if 'storage.googleapis.com' in parsed_url.netloc:
                            path_parts = parsed_url.path.strip('/').split('/', 1)
                            if len(path_parts) > 1:
                                old_blob_name = path_parts[1]
                                old_blob = bucket.blob(old_blob_name)
                                if old_blob.exists():
                                    old_blob.delete()
                                    logger.info(f"[ProfileImage] Deleted old profile image: {old_blob_name}")
                    except Exception as delete_error:
                        logger.warning(f"[ProfileImage] Failed to delete old profile image: {delete_error}")

                # Generate filename for profile image
                filename = f"profiles/user_{instance.id}_{profile_image.name}"

                # Create blob and upload
                blob = bucket.blob(filename)
                blob.upload_from_file(profile_image, content_type=profile_image.content_type)

                # Get public URL
                profile_image_url = blob.public_url
                logger.info(f"[ProfileImage] Uploaded profile image for user {instance.id}: {profile_image_url}")

                # Update user profile_image field
                instance.profile_image = profile_image_url
                instance.save(update_fields=["profile_image"])

            except Exception as e:
                logger.error(f"[ProfileImage] Failed to upload profile image for user {instance.id}: {e}", exc_info=True)
                raise serializers.ValidationError(f"Failed to upload profile image: {str(e)}")

        # If signature_image provided, save to Artist profile
        if signature_image:
            # Get or create artist profile
            artist_profile, created = Artist.objects.get_or_create(user=instance)

            try:
                # Initialize GCS client
                storage_client = storage.Client()
                bucket = storage_client.bucket(settings.GCS_BUCKET_NAME)

                # Delete old signature if exists
                old_signature_url = artist_profile.signature_image_url
                if old_signature_url:
                    try:
                        # Extract blob name from URL
                        # URL format: https://storage.googleapis.com/bucket-name/path/to/file
                        parsed_url = urlparse(old_signature_url)
                        if 'storage.googleapis.com' in parsed_url.netloc:
                            # Get path after bucket name
                            path_parts = parsed_url.path.strip('/').split('/', 1)
                            if len(path_parts) > 1:
                                old_blob_name = path_parts[1]
                                old_blob = bucket.blob(old_blob_name)
                                if old_blob.exists():
                                    old_blob.delete()
                                    logger.info(f"[Signature] Deleted old signature: {old_blob_name}")
                    except Exception as delete_error:
                        logger.warning(f"[Signature] Failed to delete old signature: {delete_error}")
                        # Don't fail the upload if deletion fails

                # Generate filename
                filename = f"signatures/user_{instance.id}_{signature_image.name}"

                # Create blob and upload
                blob = bucket.blob(filename)
                blob.upload_from_file(signature_image, content_type=signature_image.content_type)

                # Get public URL (bucket must have public access configured)
                # Note: blob.make_public() cannot be used with Uniform Bucket-Level Access
                signature_url = blob.public_url

                logger.info(f"[Signature] Uploaded signature for user {instance.id}: {signature_url}")

                # Update artist profile
                artist_profile.signature_image_url = signature_url
                artist_profile.save()

            except Exception as e:
                logger.error(f"[Signature] Failed to upload signature for user {instance.id}: {e}", exc_info=True)
                raise serializers.ValidationError(f"Failed to upload signature: {str(e)}")

        return instance
