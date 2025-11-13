"""
Tests for webhook endpoints
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
def webhook_headers(settings):
    """Headers required for webhook authentication"""
    settings.INTERNAL_API_TOKEN = "test-webhook-token"
    return {
        "HTTP_AUTHORIZATION": "Bearer test-webhook-token",
        "HTTP_X_REQUEST_SOURCE": "training-server",
    }


@pytest.mark.django_db
class TestWebhookAuthentication:
    """Test webhook authentication middleware"""

    def test_webhook_without_auth_returns_401(self, api_client):
        """Webhook request without Authorization header should return 401"""
        url = reverse("webhook_training_progress")
        response = api_client.patch(url, {"style_id": 1, "progress": {}}, format="json")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_webhook_with_invalid_token_returns_401(self, api_client, settings):
        """Webhook request with invalid token should return 401"""
        settings.INTERNAL_API_TOKEN = "correct-token"
        url = reverse("webhook_training_progress")
        response = api_client.patch(
            url,
            {"style_id": 1, "progress": {}},
            format="json",
            HTTP_AUTHORIZATION="Bearer wrong-token",
            HTTP_X_REQUEST_SOURCE="training-server",
        )
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_webhook_with_invalid_source_returns_403(self, api_client, settings):
        """Webhook request with invalid X-Request-Source should return 403"""
        settings.INTERNAL_API_TOKEN = "test-token"
        url = reverse("webhook_training_progress")
        response = api_client.patch(
            url,
            {"style_id": 1, "progress": {}},
            format="json",
            HTTP_AUTHORIZATION="Bearer test-token",
            HTTP_X_REQUEST_SOURCE="unknown-server",
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN


@pytest.mark.django_db
class TestTrainingWebhooks:
    """Test training webhook endpoints"""

    def test_training_progress_updates_style(self, api_client, webhook_headers):
        """Training progress webhook should update style training_progress"""
        # Create a test style
        user = User.objects.create(username="artist", email="artist@test.com")
        style = Style.objects.create(
            user=user,
            name="Test Style",
            training_status="processing",
        )

        url = reverse("webhook_training_progress")
        payload = {
            "style_id": style.id,
            "progress": {
                "current_epoch": 50,
                "total_epochs": 100,
                "progress_percent": 50,
                "estimated_seconds": 900,
            },
        }

        response = api_client.patch(url, payload, format="json", **webhook_headers)
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True

        # Verify style was updated
        style.refresh_from_db()
        assert style.training_progress == payload["progress"]

    def test_training_complete_updates_style_and_creates_notification(
        self, api_client, webhook_headers
    ):
        """Training complete webhook should update style and create notification"""
        user = User.objects.create(username="artist", email="artist@test.com")
        style = Style.objects.create(
            user=user,
            name="Test Style",
            training_status="processing",
        )

        url = reverse("webhook_training_complete")
        payload = {
            "style_id": style.id,
            "model_path": "gs://bucket/models/style-1/lora_weights.safetensors",
            "training_metric": {"loss": 0.05, "epochs": 100},
        }

        response = api_client.post(url, payload, format="json", **webhook_headers)
        assert response.status_code == status.HTTP_200_OK

        # Verify style was updated
        style.refresh_from_db()
        assert style.training_status == "completed"
        assert style.model_path == payload["model_path"]
        assert style.training_metric == payload["training_metric"]
        assert style.training_progress is None

        # Verify notification was created
        assert user.received_notifications.filter(
            type="style_training_complete"
        ).exists()


@pytest.mark.django_db
class TestInferenceWebhooks:
    """Test inference webhook endpoints"""

    def test_inference_complete_updates_generation(self, api_client, webhook_headers):
        """Inference complete webhook should update generation"""
        user = User.objects.create(
            username="user", email="user@test.com", token_balance=100
        )
        style = Style.objects.create(
            user=user,
            name="Test Style",
            training_status="completed",
            model_path="gs://bucket/model.safetensors",
        )
        generation = Generation.objects.create(
            user=user,
            style=style,
            cost=50,
            status="processing",
        )

        webhook_headers["HTTP_X_REQUEST_SOURCE"] = "inference-server"
        url = reverse("webhook_inference_complete")
        payload = {
            "generation_id": generation.id,
            "result_url": "https://storage.googleapis.com/bucket/result.jpg",
            "metadata": {"seed": 42, "steps": 50},
        }

        response = api_client.post(url, payload, format="json", **webhook_headers)
        assert response.status_code == status.HTTP_200_OK

        # Verify generation was updated
        generation.refresh_from_db()
        assert generation.status == "completed"
        assert generation.result_url == payload["result_url"]
        assert generation.generation_progress is None

    def test_inference_failed_refunds_tokens(self, api_client, webhook_headers):
        """Inference failed webhook should refund tokens"""
        user = User.objects.create(
            username="user", email="user@test.com", token_balance=50
        )
        style = Style.objects.create(
            user=user,
            name="Test Style",
            training_status="completed",
            model_path="gs://bucket/model.safetensors",
        )
        generation = Generation.objects.create(
            user=user,
            style=style,
            cost=50,
            status="processing",
        )

        initial_balance = user.token_balance

        webhook_headers["HTTP_X_REQUEST_SOURCE"] = "inference-server"
        url = reverse("webhook_inference_failed")
        payload = {
            "generation_id": generation.id,
            "error_message": "GPU out of memory",
            "error_code": "OOM_ERROR",
        }

        response = api_client.post(url, payload, format="json", **webhook_headers)
        assert response.status_code == status.HTTP_200_OK

        # Verify generation was updated
        generation.refresh_from_db()
        assert generation.status == "failed"
        assert generation.metadata["error_message"] == payload["error_message"]

        # Verify tokens were refunded
        user.refresh_from_db()
        assert user.token_balance == initial_balance + generation.cost
