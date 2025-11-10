from django.db import models
from django.utils import timezone


class Notification(models.Model):
    """Notification model for user notifications."""

    TYPE_CHOICES = [
        ('follow', 'Follow'),
        ('like', 'Like'),
        ('comment', 'Comment'),
        ('generation_complete', 'Generation Complete'),
        ('generation_failed', 'Generation Failed'),
        ('style_training_complete', 'Style Training Complete'),
        ('style_training_failed', 'Style Training Failed'),
    ]

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Foreign keys
    recipient = models.ForeignKey(
        'app.User',
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    actor = models.ForeignKey(
        'app.User',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='actions'
    )

    # Notification details
    type = models.CharField(max_length=30, choices=TYPE_CHOICES)
    target_type = models.CharField(max_length=30, null=True, blank=True)
    target_id = models.BigIntegerField(null=True, blank=True)

    # Status
    is_read = models.BooleanField(default=False)

    # Additional data
    metadata = models.JSONField(null=True, blank=True)

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'notifications'
        constraints = [
            models.CheckConstraint(
                check=models.Q(type__in=[
                    'follow', 'like', 'comment',
                    'generation_complete', 'generation_failed',
                    'style_training_complete', 'style_training_failed'
                ]),
                name='valid_notification_type'
            ),
        ]
        indexes = [
            models.Index(fields=['recipient', 'is_read', '-created_at'], name='idx_notifications_recipient'),
            models.Index(fields=['actor'], name='idx_notifications_actor'),
        ]

    def __str__(self):
        actor_name = self.actor.username if self.actor else 'System'
        return f"{self.type} notification for {self.recipient.username} from {actor_name}"
