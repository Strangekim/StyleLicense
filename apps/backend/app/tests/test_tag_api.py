"""
Tests for Tag System API (M2-Tag-API).

Tests:
- GET /api/tags/ - List popular tags
- GET /api/tags/?search=water - Autocomplete search
- Tag filtering in Style Model API (AND logic)
- Public access (no authentication required)
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from app.models import User, Style, Tag, StyleTag


class TestTagAPI(TestCase):
    """Test Tag API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()

        # Create artist user
        self.artist = User.objects.create_user(
            username="artist",
            email="artist@example.com",
            provider="google",
            provider_user_id="artist123",
            role="artist",
            token_balance=5000,
        )

        # Create tags with different usage counts
        self.tag_watercolor = Tag.objects.create(name="watercolor", usage_count=50)
        self.tag_portrait = Tag.objects.create(name="portrait", usage_count=30)
        self.tag_landscape = Tag.objects.create(name="landscape", usage_count=20)
        self.tag_realistic = Tag.objects.create(name="realistic", usage_count=10)
        self.tag_unused = Tag.objects.create(name="unused", usage_count=0)  # Not shown
        self.tag_inactive = Tag.objects.create(
            name="inactive", usage_count=100, is_active=False
        )  # Not shown

        # Create styles with tags
        self.style1 = Style.objects.create(
            artist=self.artist,
            name="Watercolor Portraits",
            training_status="completed",
            generation_cost_tokens=100,
        )
        StyleTag.objects.create(style=self.style1, tag=self.tag_watercolor, sequence=0)
        StyleTag.objects.create(style=self.style1, tag=self.tag_portrait, sequence=1)

        self.style2 = Style.objects.create(
            artist=self.artist,
            name="Watercolor Landscapes",
            training_status="completed",
            generation_cost_tokens=150,
        )
        StyleTag.objects.create(style=self.style2, tag=self.tag_watercolor, sequence=0)
        StyleTag.objects.create(style=self.style2, tag=self.tag_landscape, sequence=1)

    def test_list_tags_public_access(self):
        """Anonymous users can list tags."""
        response = self.client.get("/api/tags/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("data", response.data)

    def test_list_tags_returns_popular_tags(self):
        """List returns only tags with usage_count > 0."""
        response = self.client.get("/api/tags/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tags = response.data["data"]

        # Should have 4 tags (usage_count > 0)
        # unused (0) and inactive (False) should not be included
        self.assertEqual(len(tags), 4)

        # Verify all tags have usage_count > 0
        for tag in tags:
            self.assertGreater(tag["usage_count"], 0)

        # Verify tags are sorted by usage_count DESC
        tag_names = [tag["name"] for tag in tags]
        self.assertEqual(tag_names[0], "watercolor")  # 50 uses
        self.assertEqual(tag_names[1], "portrait")  # 30 uses
        self.assertEqual(tag_names[2], "landscape")  # 20 uses
        self.assertEqual(tag_names[3], "realistic")  # 10 uses

    def test_list_tags_excludes_inactive(self):
        """Inactive tags are not shown."""
        response = self.client.get("/api/tags/")

        tags = response.data["data"]
        tag_names = [tag["name"] for tag in tags]

        # inactive tag should not be in list
        self.assertNotIn("inactive", tag_names)

    def test_list_tags_excludes_unused(self):
        """Tags with usage_count = 0 are not shown."""
        response = self.client.get("/api/tags/")

        tags = response.data["data"]
        tag_names = [tag["name"] for tag in tags]

        # unused tag should not be in list
        self.assertNotIn("unused", tag_names)

    def test_tag_search_autocomplete(self):
        """Search tags by name (autocomplete)."""
        # Search for "water"
        response = self.client.get("/api/tags/?search=water")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tags = response.data["data"]

        # Should only return "watercolor"
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]["name"], "watercolor")

    def test_tag_search_case_insensitive(self):
        """Search is case-insensitive."""
        # Search with uppercase
        response = self.client.get("/api/tags/?search=WATER")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tags = response.data["data"]

        # Should still return "watercolor"
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]["name"], "watercolor")

    def test_tag_search_partial_match(self):
        """Search supports partial matching."""
        # Search for "land"
        response = self.client.get("/api/tags/?search=land")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tags = response.data["data"]

        # Should return "landscape"
        self.assertEqual(len(tags), 1)
        self.assertEqual(tags[0]["name"], "landscape")

    def test_tag_search_no_results(self):
        """Search with no matches returns empty list."""
        response = self.client.get("/api/tags/?search=nonexistent")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        tags = response.data["data"]
        self.assertEqual(len(tags), 0)

    def test_tag_detail(self):
        """Can retrieve tag detail."""
        response = self.client.get(f"/api/tags/{self.tag_watercolor.id}/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        data = response.data["data"]

        self.assertEqual(data["id"], self.tag_watercolor.id)
        self.assertEqual(data["name"], "watercolor")
        self.assertEqual(data["usage_count"], 50)

    def test_style_filtering_with_tags_and_logic(self):
        """Test that style filtering with multiple tags uses AND logic."""
        # Filter styles by watercolor AND portrait
        response = self.client.get("/api/models/?tags=watercolor,portrait")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]["results"]

        # Should only return style1 (has both watercolor AND portrait)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["name"], "Watercolor Portraits")

    def test_style_filtering_single_tag(self):
        """Test style filtering with single tag."""
        # Filter styles by watercolor only
        response = self.client.get("/api/models/?tags=watercolor")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]["results"]

        # Should return both styles (both have watercolor)
        self.assertEqual(len(results), 2)
        style_names = {style["name"] for style in results}
        self.assertIn("Watercolor Portraits", style_names)
        self.assertIn("Watercolor Landscapes", style_names)


print("Tag API tests created successfully!")
