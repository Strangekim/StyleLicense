"""
Tests for training consumer
"""

import pytest
from unittest.mock import patch, Mock, MagicMock
from consumer.training_consumer import TrainingConsumer


@patch("consumer.training_consumer.WebhookService")
@patch("consumer.training_consumer.time.sleep")  # Skip actual sleep
def test_mock_training_success(mock_sleep, mock_webhook_service, mock_training_message):
    """Test successful mock training process"""
    consumer = TrainingConsumer()

    # Extract data from mock message
    data = mock_training_message["data"]

    # Test mock_training method
    result = consumer.mock_training(
        style_id=data["style_id"],
        images=data["images"],
        num_epochs=data["parameters"]["epochs"],
    )

    assert result is True

    # Verify progress updates were sent
    assert mock_webhook_service.send_training_progress.called
    # At least one progress update should have been sent
    assert mock_webhook_service.send_training_progress.call_count >= 1


@patch("consumer.training_consumer.WebhookService")
@patch("consumer.training_consumer.time.sleep")
def test_process_training_task_success(
    mock_sleep, mock_webhook_service, mock_training_message
):
    """Test successful training task processing"""
    # Setup mocks
    mock_webhook_service.send_training_completed.return_value = True
    mock_webhook_service.send_training_progress.return_value = True

    consumer = TrainingConsumer()
    data = mock_training_message["data"]

    # Process task
    result = consumer.process_training_task(data)

    assert result is True

    # Verify completed webhook was sent
    mock_webhook_service.send_training_completed.assert_called_once()
    call_args = mock_webhook_service.send_training_completed.call_args

    # Check arguments
    assert call_args[0][0] == data["style_id"]  # style_id
    assert "lora_weights.safetensors" in call_args[0][1]  # model_path
    assert call_args[1]["loss"] == 0.05
    assert call_args[1]["epochs"] == data["parameters"]["epochs"]


@patch("consumer.training_consumer.WebhookService")
def test_process_training_task_missing_style_id(mock_webhook_service):
    """Test task processing with missing style_id"""
    consumer = TrainingConsumer()

    # Missing style_id
    data = {"images": ["gs://test/img1.jpg"], "parameters": {"epochs": 100}}

    result = consumer.process_training_task(data)

    assert result is False
    # Should not send any webhooks
    mock_webhook_service.send_training_completed.assert_not_called()
    mock_webhook_service.send_training_failed.assert_not_called()


@patch("consumer.training_consumer.WebhookService")
def test_process_training_task_missing_images(mock_webhook_service):
    """Test task processing with missing images"""
    consumer = TrainingConsumer()

    # Missing images
    data = {"style_id": 123, "parameters": {"epochs": 100}}

    result = consumer.process_training_task(data)

    assert result is False


@patch("consumer.training_consumer.WebhookService")
@patch("consumer.training_consumer.time.sleep")
def test_process_training_task_exception(mock_sleep, mock_webhook_service):
    """Test task processing with exception"""
    # Setup mock to raise exception
    mock_webhook_service.send_training_progress.side_effect = Exception("Network error")

    consumer = TrainingConsumer()

    data = {
        "style_id": 123,
        "images": ["gs://test/img1.jpg"],
        "parameters": {"epochs": 100},
    }

    result = consumer.process_training_task(data)

    assert result is False

    # Verify failure webhook was sent
    mock_webhook_service.send_training_failed.assert_called_once()
    call_args = mock_webhook_service.send_training_failed.call_args
    assert call_args[0][0] == 123  # style_id
    assert call_args[1]["error_code"] == "INTERNAL_ERROR"


def test_consumer_connect():
    """Test RabbitMQ connection setup"""
    consumer = TrainingConsumer()

    # Consumer should be initialized
    assert consumer.connection is None
    assert consumer.channel is None
    assert consumer.gcs_service is not None
