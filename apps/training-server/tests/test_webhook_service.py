"""
Tests for webhook service
"""

import pytest
from unittest.mock import patch, Mock
from services.webhook_service import WebhookService


@patch("services.webhook_service.requests.patch")
def test_send_training_status_success(mock_patch):
    """Test successful training status webhook"""
    # Setup mock
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    # Test
    result = WebhookService.send_training_status(
        style_id=1, status="processing", progress=50
    )

    # Assertions
    assert result is True
    mock_patch.assert_called_once()
    call_args = mock_patch.call_args

    # Check URL
    assert "/api/webhooks/training/1/status" in call_args[0][0]

    # Check payload
    payload = call_args[1]["json"]
    assert payload["training_status"] == "processing"
    assert payload["progress"] == 50


@patch("services.webhook_service.requests.patch")
def test_send_training_started(mock_patch):
    """Test training started notification"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    result = WebhookService.send_training_started(style_id=1)

    assert result is True
    payload = mock_patch.call_args[1]["json"]
    assert payload["training_status"] == "processing"
    assert payload["progress"] == 0


@patch("services.webhook_service.requests.patch")
def test_send_training_completed(mock_patch):
    """Test training completed notification"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    model_path = "gs://bucket/models/style-1/lora_weights.safetensors"
    result = WebhookService.send_training_completed(style_id=1, model_path=model_path)

    assert result is True
    payload = mock_patch.call_args[1]["json"]
    assert payload["training_status"] == "completed"
    assert payload["progress"] == 100
    assert payload["model_path"] == model_path


@patch("services.webhook_service.requests.patch")
def test_send_training_failed(mock_patch):
    """Test training failed notification"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    failure_reason = "Out of memory"
    result = WebhookService.send_training_failed(
        style_id=1, failure_reason=failure_reason
    )

    assert result is True
    payload = mock_patch.call_args[1]["json"]
    assert payload["training_status"] == "failed"
    assert payload["failure_reason"] == failure_reason


@patch("services.webhook_service.requests.patch")
def test_send_training_status_failure(mock_patch):
    """Test webhook failure handling"""
    # Setup mock to raise exception
    mock_patch.side_effect = Exception("Connection error")

    # Test
    result = WebhookService.send_training_status(
        style_id=1, status="processing", progress=50
    )

    # Should return False on error
    assert result is False
