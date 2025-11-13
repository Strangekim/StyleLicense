"""
Tests for Community API (Feed, Like, Comment, Follow).
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework import status

from app.models import Generation, Style, Like, Comment, Follow

User = get_user_model()


class FeedAPITests(TestCase):
    """Test Feed API endpoint."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        # Create users
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

        # Create styles
        self.style = Style.objects.create(
            artist=self.user1,
            name="Test Style",
            training_status="completed",
            generation_cost_tokens=10,
        )

        # Create public completed generations
        self.gen1 = Generation.objects.create(
            user=self.user1,
            style=self.style,
            status="completed",
            is_public=True,
            description="Public generation 1",
            result_url="https://example.com/image1.jpg",
        )
        self.gen2 = Generation.objects.create(
            user=self.user2,
            style=self.style,
            status="completed",
            is_public=True,
            description="Public generation 2",
            result_url="https://example.com/image2.jpg",
        )

        # Create private generation (should not appear in feed)
        self.gen_private = Generation.objects.create(
            user=self.user1,
            style=self.style,
            status="completed",
            is_public=False,
            description="Private generation",
        )

        # Create processing generation (should not appear in feed)
        self.gen_processing = Generation.objects.create(
            user=self.user1,
            style=self.style,
            status="processing",
            is_public=True,
            description="Processing generation",
        )

    def test_feed_list_unauthenticated(self):
        """Test that unauthenticated users can view feed."""
        response = self.client.get("/api/community/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_feed_only_shows_public_completed(self):
        """Test that feed only shows public completed generations."""
        response = self.client.get("/api/community/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

        ids = [item["id"] for item in response.data["results"]]
        self.assertIn(self.gen1.id, ids)
        self.assertIn(self.gen2.id, ids)
        self.assertNotIn(self.gen_private.id, ids)
        self.assertNotIn(self.gen_processing.id, ids)

    def test_feed_ordering(self):
        """Test that feed is ordered by created_at DESC."""
        response = self.client.get("/api/community/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Most recent first
        self.assertEqual(response.data["results"][0]["id"], self.gen2.id)
        self.assertEqual(response.data["results"][1]["id"], self.gen1.id)


class ImageDetailAPITests(TestCase):
    """Test Image detail API."""

    def setUp(self):
        """Set up test data."""
        self.client = APIClient()

        self.user = User.objects.create_user(
            username="user1",
            email="user1@test.com",
            provider="google",
            provider_user_id="google-user1",
        )

        self.style = Style.objects.create(
            artist=self.user,
            name="Test Style",
            training_status="completed",
            generation_cost_tokens=10,
        )

        self.generation = Generation.objects.create(
            user=self.user,
            style=self.style,
            status="completed",
            is_public=True,
            description="Test generation",
            result_url="https://example.com/image.jpg",
            like_count=5,
            comment_count=3,
        )

    def test_get_image_detail(self):
        """Test retrieving image detail."""
        response = self.client.get(f"/api/images/{self.generation.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["id"], self.generation.id)
        self.assertEqual(response.data["description"], "Test generation")
        self.assertEqual(response.data["like_count"], 5)
        self.assertEqual(response.data["comment_count"], 3)
        self.assertIn("user", response.data)
        self.assertIn("style", response.data)

    def test_get_private_image_returns_404(self):
        """Test that private images return 404."""
        private_gen = Generation.objects.create(
            user=self.user,
            style=self.style,
            status="completed",
            is_public=False,
            description="Private",
        )

        response = self.client.get(f"/api/images/{private_gen.id}/")
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class LikeAPITests(TestCase):
    """Test Like API."""

    def setUp(self):
        """Set up test data."""
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
            is_public=True,
            like_count=0,
        )

    def test_like_toggle_requires_authentication(self):
        """Test that like requires authentication."""
        response = self.client.post(f"/api/images/{self.generation.id}/like/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_like_generation(self):
        """Test liking a generation."""
        self.client.force_authenticate(user=self.user2)
        response = self.client.post(f"/api/images/{self.generation.id}/like/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_liked"])
        self.assertEqual(response.data["like_count"], 1)

        # Verify in database
        self.generation.refresh_from_db()
        self.assertEqual(self.generation.like_count, 1)
        self.assertTrue(
            Like.objects.filter(user=self.user2, generation=self.generation).exists()
        )

    def test_unlike_generation(self):
        """Test unliking a generation."""
        self.client.force_authenticate(user=self.user2)

        # First like
        self.client.post(f"/api/images/{self.generation.id}/like/")

        # Then unlike
        response = self.client.post(f"/api/images/{self.generation.id}/like/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_liked"])
        self.assertEqual(response.data["like_count"], 0)

        # Verify in database
        self.generation.refresh_from_db()
        self.assertEqual(self.generation.like_count, 0)
        self.assertFalse(
            Like.objects.filter(user=self.user2, generation=self.generation).exists()
        )


class CommentAPITests(TestCase):
    """Test Comment API."""

    def setUp(self):
        """Set up test data."""
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
            is_public=True,
            comment_count=0,
        )

    def test_list_comments(self):
        """Test listing comments for a generation."""
        Comment.objects.create(
            user=self.user1, generation=self.generation, content="Comment 1"
        )
        Comment.objects.create(
            user=self.user2, generation=self.generation, content="Comment 2"
        )

        response = self.client.get(f"/api/images/{self.generation.id}/comments/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 2)

    def test_add_comment_requires_authentication(self):
        """Test that adding comment requires authentication."""
        response = self.client.post(
            f"/api/images/{self.generation.id}/comments/", {"content": "Test comment"}
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_add_comment(self):
        """Test adding a comment."""
        self.client.force_authenticate(user=self.user2)

        response = self.client.post(
            f"/api/images/{self.generation.id}/comments/", {"content": "Great work!"}
        )

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["content"], "Great work!")
        self.assertEqual(response.data["user"]["username"], "user2")

        # Verify comment count updated
        self.generation.refresh_from_db()
        self.assertEqual(self.generation.comment_count, 1)

    def test_add_comment_validation(self):
        """Test comment content validation."""
        self.client.force_authenticate(user=self.user2)

        # Empty content
        response = self.client.post(
            f"/api/images/{self.generation.id}/comments/", {"content": ""}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Too long content (> 500 chars)
        response = self.client.post(
            f"/api/images/{self.generation.id}/comments/", {"content": "a" * 501}
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_delete_comment_owner(self):
        """Test deleting own comment."""
        self.client.force_authenticate(user=self.user2)

        # Create comment
        comment = Comment.objects.create(
            user=self.user2, generation=self.generation, content="My comment"
        )
        self.generation.comment_count = 1
        self.generation.save()

        # Delete comment
        response = self.client.delete(f"/api/comments/{comment.id}/")

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

        # Verify deleted
        self.assertFalse(Comment.objects.filter(id=comment.id).exists())

        # Verify comment count updated
        self.generation.refresh_from_db()
        self.assertEqual(self.generation.comment_count, 0)

    def test_delete_comment_non_owner(self):
        """Test that non-owner cannot delete comment."""
        comment = Comment.objects.create(
            user=self.user1, generation=self.generation, content="User1 comment"
        )

        # Try to delete as user2
        self.client.force_authenticate(user=self.user2)
        response = self.client.delete(f"/api/comments/{comment.id}/")

        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class FollowAPITests(TestCase):
    """Test Follow API."""

    def setUp(self):
        """Set up test data."""
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

    def test_follow_requires_authentication(self):
        """Test that follow requires authentication."""
        response = self.client.post(f"/api/users/{self.user2.id}/follow/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_follow_user(self):
        """Test following a user."""
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(f"/api/users/{self.user2.id}/follow/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["is_following"])
        self.assertEqual(response.data["follower_count"], 1)

        # Verify in database
        self.assertTrue(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

    def test_unfollow_user(self):
        """Test unfollowing a user."""
        self.client.force_authenticate(user=self.user1)

        # First follow
        self.client.post(f"/api/users/{self.user2.id}/follow/")

        # Then unfollow
        response = self.client.post(f"/api/users/{self.user2.id}/follow/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data["is_following"])
        self.assertEqual(response.data["follower_count"], 0)

        # Verify in database
        self.assertFalse(
            Follow.objects.filter(follower=self.user1, following=self.user2).exists()
        )

    def test_cannot_follow_self(self):
        """Test that user cannot follow themselves."""
        self.client.force_authenticate(user=self.user1)

        response = self.client.post(f"/api/users/{self.user1.id}/follow/")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_list_following(self):
        """Test listing users that current user follows."""
        self.client.force_authenticate(user=self.user1)

        # Follow user2
        Follow.objects.create(follower=self.user1, following=self.user2)

        response = self.client.get("/api/users/following/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 1)
        self.assertEqual(response.data["results"][0]["username"], "user2")

    def test_list_following_requires_authentication(self):
        """Test that listing following requires authentication."""
        response = self.client.get("/api/users/following/")
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
