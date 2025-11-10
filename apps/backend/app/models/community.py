from django.db import models
from django.utils import timezone


class Follow(models.Model):
    """Follow model for user-to-user relationships."""

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Foreign keys
    follower = models.ForeignKey(
        'app.User',
        on_delete=models.CASCADE,
        related_name='following'
    )
    following = models.ForeignKey(
        'app.User',
        on_delete=models.CASCADE,
        related_name='followers'
    )

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'follows'
        constraints = [
            models.CheckConstraint(
                check=~models.Q(follower=models.F('following')),
                name='no_self_follow'
            ),
            models.UniqueConstraint(
                fields=['follower', 'following'],
                name='unique_follow_pair'
            ),
        ]
        indexes = [
            models.Index(fields=['follower'], name='idx_follows_follower'),
            models.Index(fields=['following'], name='idx_follows_following'),
        ]

    def __str__(self):
        return f"{self.follower.username} follows {self.following.username}"


class Like(models.Model):
    """Like model for generation likes."""

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Foreign keys
    user = models.ForeignKey(
        'app.User',
        on_delete=models.CASCADE,
        related_name='likes'
    )
    generation = models.ForeignKey(
        'app.Generation',
        on_delete=models.CASCADE,
        related_name='likes'
    )

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = 'likes'
        constraints = [
            models.UniqueConstraint(
                fields=['user', 'generation'],
                name='unique_like'
            ),
        ]
        indexes = [
            models.Index(fields=['generation'], name='idx_likes_generation'),
            models.Index(fields=['user', '-created_at'], name='idx_likes_user'),
        ]

    def __str__(self):
        return f"{self.user.username} likes Generation {self.generation.id}"


class Comment(models.Model):
    """Comment model for generation comments."""

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Foreign keys
    generation = models.ForeignKey(
        'app.Generation',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    user = models.ForeignKey(
        'app.User',
        on_delete=models.CASCADE,
        related_name='comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    # Content
    content = models.TextField()

    # Statistics (cached)
    like_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'comments'
        indexes = [
            models.Index(fields=['generation', '-created_at'], name='idx_comments_generation'),
            models.Index(fields=['user'], name='idx_comments_user'),
            models.Index(fields=['parent'], name='idx_comments_parent'),
        ]

    def __str__(self):
        return f"Comment by {self.user.username} on Generation {self.generation.id}"

    def save(self, *args, **kwargs):
        """Override save to ensure updated_at is set."""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
