"""
Serializers for Notification model.
"""
from rest_framework import serializers
from app.models import Notification


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for listing notifications."""

    actor_username = serializers.CharField(
        source="actor.username", read_only=True, allow_null=True
    )
    actor_profile_image = serializers.CharField(
        source="actor.profile_image", read_only=True, allow_null=True
    )
    message = serializers.SerializerMethodField()
    thumbnail = serializers.SerializerMethodField()

    class Meta:
        model = Notification
        fields = [
            "id",
            "type",
            "actor_username",
            "actor_profile_image",
            "target_type",
            "target_id",
            "is_read",
            "metadata",
            "message",
            "thumbnail",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "type",
            "actor_username",
            "actor_profile_image",
            "target_type",
            "target_id",
            "metadata",
            "created_at",
        ]

    def get_message(self, obj):
        """Generate notification message based on type and actor."""
        actor_name = obj.actor.username if obj.actor else "시스템"

        if obj.type == "like":
            return f"{actor_name}님이 회원님의 게시물을 좋아합니다."
        elif obj.type == "comment":
            return f"{actor_name}님이 회원님의 게시물에 댓글을 남겼습니다."
        elif obj.type == "follow":
            return f"{actor_name}님이 회원님을 팔로우했습니다."
        elif obj.type == "generation_complete":
            return "이미지 생성이 완료되었습니다."
        elif obj.type == "generation_failed":
            return "이미지 생성이 실패했습니다."
        elif obj.type == "style_training_complete":
            style_name = obj.metadata.get("style_name", "스타일") if obj.metadata else "스타일"
            return f"{style_name} 학습이 완료되었습니다."
        elif obj.type == "style_training_failed":
            style_name = obj.metadata.get("style_name", "스타일") if obj.metadata else "스타일"
            return f"{style_name} 학습이 실패했습니다."
        else:
            return "새로운 알림이 있습니다."

    def get_thumbnail(self, obj):
        """Get thumbnail image URL based on notification type."""
        if obj.metadata and "thumbnail_url" in obj.metadata:
            return obj.metadata["thumbnail_url"]
        return None


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking notification as read."""

    is_read = serializers.BooleanField(default=True)
