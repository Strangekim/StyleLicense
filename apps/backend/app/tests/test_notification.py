"""
Tests for Notification API and signals.
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from app.models import Notification, Like, Comment, Follow, Generation, Style

User = get_user_model()


class NotificationSignalTests(TestCase):
    """Test notification creation via signals."""

    def setUp(self):
        """Set up test data."""
        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@test.com",
            provider="google",
            provider_user_id="google-user1",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@test.com",
            provider="google",
            provider_user_id="google-user2",
        )

        # Create a style and generation for testing
        self.style = Style.objects.create(
            artist=self.user1,
            name="Test Style",
            training_status="completed",
            generation_cost_tokens=10,
        )
        self.generation = Generation.objects.create(
            user=self.user1,
            style=self.style,
            status="completed",
            description="Test generation",
        )

    def test_like_creates_notification(self):
        """Test that liking a generation creates a notification."""
        # user2 likes user1's generation
        like = Like.objects.create(user=self.user2, generation=self.generation)

        # Check notification was created
        notification = Notification.objects.filter(
            recipient=self.user1,
            actor=self.user2,
            type="like",
            target_type="generation",
            target_id=self.generation.id,
        ).first()

        self.assertIsNotNone(notification)
        self.assertEqual(notification.is_read, False)
        self.assertIn("generation_description", notification.metadata)

    def test_self_like_does_not_create_notification(self):
        """Test that user liking their own generation does not create notification."""
        # user1 likes their own generation
        Like.objects.create(user=self.user1, generation=self.generation)

        # No notification should be created
        notification_count = Notification.objects.filter(
            recipient=self.user1, type="like"
        ).count()

        self.assertEqual(notification_count, 0)

    def test_comment_creates_notification(self):
        """Test that commenting on a generation creates a notification."""
        # user2 comments on user1's generation
        comment = Comment.objects.create(
            user=self.user2, generation=self.generation, content="Great work!"
        )

        # Check notification was created
        notification = Notification.objects.filter(
            recipient=self.user1,
            actor=self.user2,
            type="comment",
            target_type="generation",
            target_id=self.generation.id,
        ).first()

        self.assertIsNotNone(notification)
        self.assertEqual(notification.metadata["comment_preview"], "Great work!")

    def test_self_comment_does_not_create_notification(self):
        """Test that user commenting on their own generation does not create notification."""
        # user1 comments on their own generation
        Comment.objects.create(
            user=self.user1, generation=self.generation, content="Thanks!"
        )

        # No notification should be created
        notification_count = Notification.objects.filter(
            recipient=self.user1, type="comment"
        ).count()

        self.assertEqual(notification_count, 0)

    def test_follow_creates_notification(self):
        """Test that following a user creates a notification."""
        # user2 follows user1
        follow = Follow.objects.create(follower=self.user2, following=self.user1)

        # Check notification was created
        notification = Notification.objects.filter(
            recipient=self.user1,
            actor=self.user2,
            type="follow",
            target_type="user",
            target_id=self.user2.id,
        ).first()

        self.assertIsNotNone(notification)
        self.assertEqual(notification.metadata["follower_username"], "user2")


class NotificationAPITests(TestCase):
    """Test Notification API endpoints."""

    def setUp(self):
        """Set up test data and API client."""
        self.client = APIClient()

        self.user1 = User.objects.create_user(
            username="user1",
            email="user1@test.com",
            provider="google",
            provider_user_id="google-user1",
        )
        self.user2 = User.objects.create_user(
            username="user2",
            email="user2@test.com",
            provider="google",
            provider_user_id="google-user2",
        )

        # Create notifications for user1
        self.notif1 = Notification.objects.create(
            recipient=self.user1,
            actor=self.user2,
            type="follow",
            target_type="user",
            target_id=self.user2.id,
        )
        self.notif2 = Notification.objects.create(
            recipient=self.user1,
            actor=self.user2,
            type="like",
            target_type="generation",
            target_id=1,
            is_read=True,
        )
        # Notification for user2 (should not appear in user1's list)
        Notification.objects.create(
            recipient=self.user2,
            actor=self.user1,
            type="follow",
            target_type="user",
            target_id=self.user1.id,
        )

    def test_list_notifications_unauthenticated(self):
        """Test that unauthenticated user cannot access notifications."""
        response = self.client.get("/api/notifications/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_list_notifications(self):
        """Test listing notifications for authenticated user."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/notifications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)
        self.assertEqual(response.data["unread_count"], 1)

    def test_list_unread_notifications_only(self):
        """Test filtering unread notifications."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.get("/api/notifications/?unread_only=true")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["id"], self.notif1.id)

    def test_mark_notification_as_read(self):
        """Test marking a notification as read."""
        self.client.force_authenticate(user=self.user1)
        response = self.client.patch(
            f"/api/notifications/{self.notif1.id}/read/", {"is_read": True}
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["is_read"], True)

        # Verify in database
        self.notif1.refresh_from_db()
        self.assertTrue(self.notif1.is_read)

    def test_mark_other_users_notification_forbidden(self):
        """Test that user cannot mark another user's notification."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.patch(
            f"/api/notifications/{self.notif1.id}/read/", {"is_read": True}
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_mark_all_as_read(self):
        """Test marking all notifications as read."""
        self.client.force_authenticate(user=self.user1)

        # Create more unread notifications
        Notification.objects.create(
            recipient=self.user1,
            actor=self.user2,
            type="like",
            target_type="generation",
            target_id=2,
        )

        response = self.client.post("/api/notifications/mark-all-read/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["updated_count"], 2)  # notif1 + new notification

        # Verify all are read
        unread_count = Notification.objects.filter(
            recipient=self.user1, is_read=False
        ).count()
        self.assertEqual(unread_count, 0)

    def test_notification_ordering(self):
        """Test that notifications are ordered by created_at DESC."""
        self.client.force_authenticate(user=self.user1)

        # Create a newer notification
        new_notif = Notification.objects.create(
            recipient=self.user1,
            actor=self.user2,
            type="comment",
            target_type="generation",
            target_id=1,
        )

        response = self.client.get("/api/notifications/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Newest should be first
        self.assertEqual(response.data["results"][0]["id"], new_notif.id)
