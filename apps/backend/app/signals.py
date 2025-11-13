"""
Django signals for automatic notification creation.

This module contains signal handlers that create notifications
when community events occur (like, comment, follow).
"""
from django.db.models.signals import post_save
from django.dispatch import receiver

from app.models import Like, Comment, Follow, Notification


@receiver(post_save, sender=Like)
def create_like_notification(sender, instance, created, **kwargs):
    """Create notification when someone likes a generation.

    Args:
        sender: Like model class
        instance: Like instance that was saved
        created: True if this is a new like (not an update)
        **kwargs: Additional signal arguments
    """
    if not created:
        return

    # Don't notify if user likes their own generation
    if instance.user == instance.generation.user:
        return

    Notification.objects.create(
        recipient=instance.generation.user,
        actor=instance.user,
        type="like",
        target_type="generation",
        target_id=instance.generation.id,
        metadata={
            "generation_description": instance.generation.description[:100]
            if instance.generation.description
            else None,
        },
    )


@receiver(post_save, sender=Comment)
def create_comment_notification(sender, instance, created, **kwargs):
    """Create notification when someone comments on a generation.

    Args:
        sender: Comment model class
        instance: Comment instance that was saved
        created: True if this is a new comment (not an update)
        **kwargs: Additional signal arguments
    """
    if not created:
        return

    # Don't notify if user comments on their own generation
    if instance.user == instance.generation.user:
        return

    Notification.objects.create(
        recipient=instance.generation.user,
        actor=instance.user,
        type="comment",
        target_type="generation",
        target_id=instance.generation.id,
        metadata={
            "comment_preview": instance.content[:100],
            "parent_id": instance.parent.id if instance.parent else None,
        },
    )


@receiver(post_save, sender=Follow)
def create_follow_notification(sender, instance, created, **kwargs):
    """Create notification when someone follows a user.

    Args:
        sender: Follow model class
        instance: Follow instance that was saved
        created: True if this is a new follow (not an update)
        **kwargs: Additional signal arguments
    """
    if not created:
        return

    Notification.objects.create(
        recipient=instance.following,
        actor=instance.follower,
        type="follow",
        target_type="user",
        target_id=instance.follower.id,
        metadata={
            "follower_username": instance.follower.username,
        },
    )
