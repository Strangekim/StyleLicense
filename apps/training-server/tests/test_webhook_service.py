"""
Tests for webhook service
"""

import pytest
from unittest.mock import patch, Mock
from services.webhook_service import WebhookService


@patch("services.webhook_service.requests.patch")
def test_send_training_progress(mock_patch):
    """Test training progress webhook (API: PATCH /api/webhooks/training/progress)"""
    # Setup mock
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    # Test
    result = WebhookService.send_training_progress(
        style_id=10,
        current_epoch=50,
        total_epochs=100,
        progress_percent=50,
        estimated_seconds=900,
    )

    # Assertions
    assert result is True
    mock_patch.assert_called_once()
    call_args = mock_patch.call_args

    # Check URL
    assert call_args[0][0] == "http://localhost:8000/api/webhooks/training/progress"

    # Check payload matches API.md spec
    payload = call_args[1]["json"]
    assert payload["style_id"] == 10
    assert payload["progress"]["current_epoch"] == 50
    assert payload["progress"]["total_epochs"] == 100
    assert payload["progress"]["progress_percent"] == 50
    assert payload["progress"]["estimated_seconds"] == 900

    # Check headers
    headers = call_args[1]["headers"]
    assert headers["Authorization"].startswith("Bearer ")
    assert headers["X-Request-Source"] == "training-server"


@patch("services.webhook_service.requests.post")
def test_send_training_completed(mock_post):
    """Test training completed webhook (API: POST /api/webhooks/training/complete)"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    model_path = "gs://test-bucket/models/style-10/lora_weights.safetensors"
    result = WebhookService.send_training_completed(
        style_id=10, model_path=model_path, loss=0.05, epochs=100
    )

    assert result is True
    call_args = mock_post.call_args

    # Check URL
    assert call_args[0][0] == "http://localhost:8000/api/webhooks/training/complete"

    # Check payload matches API.md spec
    payload = call_args[1]["json"]
    assert payload["style_id"] == 10
    assert payload["model_path"] == model_path
    assert payload["training_metric"]["loss"] == 0.05
    assert payload["training_metric"]["epochs"] == 100


@patch("services.webhook_service.requests.post")
def test_send_training_completed_minimal(mock_post):
    """Test training completed webhook without optional training_metric"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    model_path = "gs://test-bucket/models/style-10/lora_weights.safetensors"
    result = WebhookService.send_training_completed(style_id=10, model_path=model_path)

    assert result is True
    payload = mock_post.call_args[1]["json"]
    assert payload["style_id"] == 10
    assert payload["model_path"] == model_path
    assert "training_metric" not in payload


@patch("services.webhook_service.requests.post")
def test_send_training_failed(mock_post):
    """Test training failed webhook (API: POST /api/webhooks/training/failed)"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = WebhookService.send_training_failed(
        style_id=10,
        error_message="Insufficient training data quality",
        error_code="LOW_QUALITY_DATA",
    )

    assert result is True
    call_args = mock_post.call_args

    # Check URL
    assert call_args[0][0] == "http://localhost:8000/api/webhooks/training/failed"

    # Check payload matches API.md spec
    payload = call_args[1]["json"]
    assert payload["style_id"] == 10
    assert payload["error_message"] == "Insufficient training data quality"
    assert payload["error_code"] == "LOW_QUALITY_DATA"


@patch("services.webhook_service.requests.post")
def test_send_training_failed_default_error_code(mock_post):
    """Test training failed webhook with default error code"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = WebhookService.send_training_failed(
        style_id=10, error_message="Unknown error"
    )

    assert result is True
    payload = mock_post.call_args[1]["json"]
    assert payload["error_code"] == "TRAINING_FAILED"  # Default


@patch("services.webhook_service.requests.patch")
def test_send_training_progress_failure(mock_patch):
    """Test webhook failure handling"""
    import requests

    # Setup mock to raise RequestException
    mock_patch.side_effect = requests.exceptions.RequestException("Connection error")

    # Test
    result = WebhookService.send_training_progress(
        style_id=10,
        current_epoch=50,
        total_epochs=100,
        progress_percent=50,
        estimated_seconds=900,
    )

    # Should return False on error
    assert result is False


@patch("services.webhook_service.requests.post")
def test_send_training_completed_failure(mock_post):
    """Test training completed webhook failure handling"""
    import requests

    mock_post.side_effect = requests.exceptions.RequestException("Connection error")

    result = WebhookService.send_training_completed(
        style_id=10, model_path="gs://test/model.safetensors"
    )

    assert result is False
