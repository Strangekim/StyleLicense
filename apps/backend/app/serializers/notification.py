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


class MarkAsReadSerializer(serializers.Serializer):
    """Serializer for marking notification as read."""

    is_read = serializers.BooleanField(default=True)
