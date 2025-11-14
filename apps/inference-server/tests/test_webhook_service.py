"""
Tests for webhook service
"""

import pytest
from unittest.mock import patch, Mock
from services.webhook_service import WebhookService


@patch("services.webhook_service.requests.patch")
def test_send_inference_progress_success(mock_patch):
    """Test successful inference progress webhook"""
    # Setup mock
    mock_response = Mock()
    mock_response.status_code = 200
    mock_patch.return_value = mock_response

    # Test
    result = WebhookService.send_inference_progress(
        generation_id=1,
        current_step=25,
        total_steps=50,
        progress_percent=50,
        estimated_seconds=10,
    )

    # Assertions
    assert result is True
    mock_patch.assert_called_once()
    call_args = mock_patch.call_args

    # Check URL
    assert "/api/webhooks/inference/progress" in call_args[0][0]

    # Check payload structure
    payload = call_args[1]["json"]
    assert payload["generation_id"] == 1
    assert "progress" in payload
    assert payload["progress"]["current_step"] == 25
    assert payload["progress"]["total_steps"] == 50
    assert payload["progress"]["progress_percent"] == 50
    assert payload["progress"]["estimated_seconds"] == 10


@patch("services.webhook_service.requests.patch")
def test_send_inference_progress_failure(mock_patch):
    """Test inference progress webhook failure handling"""
    import requests

    # Setup mock to raise RequestException
    mock_patch.side_effect = requests.exceptions.RequestException("Connection error")

    # Test
    result = WebhookService.send_inference_progress(
        generation_id=1,
        current_step=25,
        total_steps=50,
        progress_percent=50,
        estimated_seconds=10,
    )

    # Should return False on error
    assert result is False


@patch("services.webhook_service.requests.post")
def test_send_inference_completed_success(mock_post):
    """Test successful inference completed webhook"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result_url = "gs://bucket/generations/gen-1.png"

    result = WebhookService.send_inference_completed(
        generation_id=1,
        result_url=result_url,
        seed=42,
        steps=50,
        guidance_scale=7.5,
    )

    assert result is True
    call_args = mock_post.call_args

    # Check URL
    assert "/api/webhooks/inference/complete" in call_args[0][0]

    # Check payload
    payload = call_args[1]["json"]
    assert payload["generation_id"] == 1
    assert payload["result_url"] == result_url
    assert "metadata" in payload
    assert payload["metadata"]["seed"] == 42
    assert payload["metadata"]["steps"] == 50
    assert payload["metadata"]["guidance_scale"] == 7.5


@patch("services.webhook_service.requests.post")
def test_send_inference_completed_minimal(mock_post):
    """Test inference completed webhook with minimal metadata"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result_url = "gs://bucket/generations/gen-1.png"

    result = WebhookService.send_inference_completed(
        generation_id=1, result_url=result_url
    )

    assert result is True
    payload = mock_post.call_args[1]["json"]
    assert payload["generation_id"] == 1
    assert payload["result_url"] == result_url
    # No metadata should be included if not provided
    assert "metadata" not in payload


@patch("services.webhook_service.requests.post")
def test_send_inference_completed_failure(mock_post):
    """Test inference completed webhook failure handling"""
    import requests

    mock_post.side_effect = requests.exceptions.RequestException("Connection error")

    result = WebhookService.send_inference_completed(
        generation_id=1, result_url="gs://bucket/image.png"
    )

    assert result is False


@patch("services.webhook_service.requests.post")
def test_send_inference_failed_success(mock_post):
    """Test successful inference failed webhook"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    error_message = "Out of GPU memory"
    error_code = "OOM_ERROR"

    result = WebhookService.send_inference_failed(
        generation_id=1, error_message=error_message, error_code=error_code
    )

    assert result is True
    call_args = mock_post.call_args

    # Check URL
    assert "/api/webhooks/inference/failed" in call_args[0][0]

    # Check payload
    payload = call_args[1]["json"]
    assert payload["generation_id"] == 1
    assert payload["error_message"] == error_message
    assert payload["error_code"] == error_code


@patch("services.webhook_service.requests.post")
def test_send_inference_failed_default_code(mock_post):
    """Test inference failed webhook with default error code"""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_post.return_value = mock_response

    result = WebhookService.send_inference_failed(
        generation_id=1, error_message="Unknown error"
    )

    assert result is True
    payload = mock_post.call_args[1]["json"]
    assert payload["error_code"] == "GENERATION_FAILED"


@patch("services.webhook_service.requests.post")
def test_send_inference_failed_failure(mock_post):
    """Test inference failed webhook failure handling"""
    import requests

    mock_post.side_effect = requests.exceptions.RequestException("Connection error")

    result = WebhookService.send_inference_failed(
        generation_id=1, error_message="Test error"
    )

    assert result is False
