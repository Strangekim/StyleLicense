"""
Tests for generation API endpoints
"""

import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from app.models.style import Style
from app.models.generation import Generation
from app.models.user import User


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def authenticated_user(api_client):
    """Create and authenticate a user"""
    user = User.objects.create(
        username="testuser", email="test@example.com", token_balance=200
    )
    api_client.force_authenticate(user=user)
    return user


@pytest.fixture
def completed_style(authenticated_user):
    """Create a completed style with model path"""
    return Style.objects.create(
        user=authenticated_user,
        name="Test Style",
        training_status="completed",
        model_path="gs://bucket/models/style-1/lora_weights.safetensors",
    )


@pytest.mark.django_db
class TestGenerationCreate:
    """Test POST /api/generations (image generation request)"""

    def test_create_generation_success(
        self, api_client, authenticated_user, completed_style
    ):
        """Creating a generation should consume tokens and return generation ID"""
        url = reverse("generation-list")
        payload = {
            "style_id": completed_style.id,
            "prompt_tags": ["woman", "portrait", "sunset"],
            "description": "Test generation",
            "aspect_ratio": "1:1",
            "seed": 42,
        }

        initial_balance = authenticated_user.token_balance

        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["success"] is True
        assert "data" in response.data
        assert response.data["data"]["status"] == "queued"
        assert response.data["data"]["consumed_tokens"] == 50  # 1:1 aspect ratio

        # Verify tokens were consumed
        authenticated_user.refresh_from_db()
        assert authenticated_user.token_balance == initial_balance - 50

        # Verify generation was created
        assert Generation.objects.filter(
            user=authenticated_user, style=completed_style
        ).exists()

    def test_create_generation_insufficient_tokens(
        self, api_client, authenticated_user, completed_style
    ):
        """Creating generation without sufficient tokens should return 402"""
        authenticated_user.token_balance = 10
        authenticated_user.save()

        url = reverse("generation-list")
        payload = {
            "style_id": completed_style.id,
            "prompt_tags": ["woman", "portrait"],
            "aspect_ratio": "1:1",
        }

        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_402_PAYMENT_REQUIRED

    def test_create_generation_style_not_ready(self, api_client, authenticated_user):
        """Creating generation with incomplete style should return 422"""
        incomplete_style = Style.objects.create(
            user=authenticated_user,
            name="Incomplete Style",
            training_status="processing",
        )

        url = reverse("generation-list")
        payload = {
            "style_id": incomplete_style.id,
            "prompt_tags": ["test"],
            "aspect_ratio": "1:1",
        }

        response = api_client.post(url, payload, format="json")
        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


@pytest.mark.django_db
class TestGenerationRetrieve:
    """Test GET /api/generations/:id (generation status polling)"""

    def test_retrieve_generation_queued(
        self, api_client, authenticated_user, completed_style
    ):
        """Retrieving queued generation should return status and progress null"""
        generation = Generation.objects.create(
            user=authenticated_user,
            style=completed_style,
            cost=50,
            status="queued",
        )

        url = reverse("generation-detail", args=[generation.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["status"] == "queued"
        assert response.data["data"]["progress"] is None

    def test_retrieve_generation_completed(
        self, api_client, authenticated_user, completed_style
    ):
        """Retrieving completed generation should return result_url"""
        generation = Generation.objects.create(
            user=authenticated_user,
            style=completed_style,
            cost=50,
            status="completed",
            result_url="https://storage.googleapis.com/bucket/result.jpg",
        )

        url = reverse("generation-detail", args=[generation.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["data"]["status"] == "completed"
        assert response.data["data"]["result_url"] == generation.result_url

    def test_retrieve_other_user_private_generation_forbidden(self, api_client):
        """Retrieving another user's private generation should return 403"""
        owner = User.objects.create(username="owner", email="owner@test.com")
        viewer = User.objects.create(username="viewer", email="viewer@test.com")
        style = Style.objects.create(
            user=owner,
            name="Style",
            training_status="completed",
            model_path="gs://bucket/model.safetensors",
        )
        generation = Generation.objects.create(
            user=owner,
            style=style,
            cost=50,
            status="completed",
            is_public=False,
        )

        api_client.force_authenticate(user=viewer)
        url = reverse("generation-detail", args=[generation.id])
        response = api_client.get(url)

        assert response.status_code == status.HTTP_403_FORBIDDEN
