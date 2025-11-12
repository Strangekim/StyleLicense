"""
Tests for webhook service
"""

import pytest
from unittest.mock import patch, Mock
from services.webhook_service import WebhookService


@patch("services.webhook_service.requests.patch")
def test_send_generation_status_success(mock_patch):
    """Test successful generation status webhook"""
    # Setup mock
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    # Test
    result = WebhookService.send_generation_status(
        generation_id=1, status="processing", progress=50
    )

    # Assertions
    assert result is True
    mock_patch.assert_called_once()
    call_args = mock_patch.call_args

    # Check URL
    assert "/api/webhooks/generation/1/status" in call_args[0][0]

    # Check payload
    payload = call_args[1]["json"]
    assert payload["generation_status"] == "processing"
    assert payload["progress"] == 50


@patch("services.webhook_service.requests.patch")
def test_send_generation_started(mock_patch):
    """Test generation started notification"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    result = WebhookService.send_generation_started(generation_id=1)

    assert result is True
    payload = mock_patch.call_args[1]["json"]
    assert payload["generation_status"] == "processing"
    assert payload["progress"] == 0


@patch("services.webhook_service.requests.patch")
def test_send_generation_completed(mock_patch):
    """Test generation completed notification"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    image_url = "gs://bucket/generations/gen-1.png"
    metadata = {"seed": 42, "steps": 50}

    result = WebhookService.send_generation_completed(
        generation_id=1, image_url=image_url, metadata=metadata
    )

    assert result is True
    payload = mock_patch.call_args[1]["json"]
    assert payload["generation_status"] == "completed"
    assert payload["progress"] == 100
    assert payload["image_url"] == image_url
    assert payload["metadata"] == metadata


@patch("services.webhook_service.requests.patch")
def test_send_generation_failed(mock_patch):
    """Test generation failed notification"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    failure_reason = "Out of GPU memory"
    result = WebhookService.send_generation_failed(
        generation_id=1, failure_reason=failure_reason
    )

    assert result is True
    payload = mock_patch.call_args[1]["json"]
    assert payload["generation_status"] == "failed"
    assert payload["failure_reason"] == failure_reason


@patch("services.webhook_service.requests.patch")
def test_send_generation_status_failure(mock_patch):
    """Test webhook failure handling"""
    import requests

    # Setup mock to raise RequestException
    mock_patch.side_effect = requests.exceptions.RequestException("Connection error")

    # Test
    result = WebhookService.send_generation_status(
        generation_id=1, status="processing", progress=50
    )

    # Should return False on error
    assert result is False
