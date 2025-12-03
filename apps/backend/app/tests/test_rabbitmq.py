"""
Tests for RabbitMQ Integration (M2-RabbitMQ-Integration).

Tests:
- Message format validation
- Queue declaration
- Message delivery to RabbitMQ
- Connection retry logic
- No connection leaks
"""
import json
import unittest
import pytest
from unittest.mock import patch, MagicMock, call
from django.conf import settings

from app.services.rabbitmq_service import RabbitMQService, get_rabbitmq_service


class TestRabbitMQService(unittest.TestCase):
    """Test RabbitMQ service functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = RabbitMQService()

    def tearDown(self):
        """Clean up after tests."""
        self.service.close()

    @patch('app.services.rabbitmq_service.pika.BlockingConnection')
    def test_queue_declaration(self, mock_connection):
        """Test that queues are declared correctly."""
        # Mock channel
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        mock_connection.return_value.is_closed = False

        # Declare queue
        self.service.declare_queue("test_queue", durable=True)

        # Verify queue_declare was called
        mock_channel.queue_declare.assert_called_once_with(
            queue="test_queue",
            durable=True
        )

    @patch('app.services.rabbitmq_service.pika.BlockingConnection')
    def test_send_training_task_message_format(self, mock_connection):
        """Test that training task messages have correct format."""
        # Mock channel
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        mock_connection.return_value.is_closed = False

        # Send training task
        image_paths = ["/path/to/image1.jpg", "/path/to/image2.jpg"]
        task_id = self.service.send_training_task(
            style_id=123,
            image_paths=image_paths,
            num_epochs=200
        )

        # Verify task_id is returned
        assert task_id is not None
        assert isinstance(task_id, str)

        # Verify basic_publish was called
        assert mock_channel.basic_publish.called

        # Get the published message
        call_args = mock_channel.basic_publish.call_args
        message_body = call_args[1]['body']
        message = json.loads(message_body)

        # Verify message format
        assert 'task_id' in message
        assert 'type' in message
        assert message['type'] == 'model_training'
        assert 'data' in message
        assert message['data']['style_id'] == 123
        assert message['data']['images'] == image_paths  # Changed from 'image_paths'
        assert 'parameters' in message['data']  # New structure
        assert message['data']['parameters']['epochs'] == 200
        assert message['data']['parameters']['learning_rate'] == 0.0001
        assert message['data']['parameters']['batch_size'] == 4
        assert 'webhook_url' in message

    @patch('app.services.rabbitmq_service.pika.BlockingConnection')
    def test_send_generation_task_message_format(self, mock_connection):
        """Test that generation task messages have correct format."""
        # Mock channel
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        mock_connection.return_value.is_closed = False

        # Send generation task
        task_id = self.service.send_generation_task(
            generation_id=456,
            style_id=123,
            lora_path="/models/style_123/lora.safetensors",
            prompt="a beautiful sunset",
            aspect_ratio="1:1",
            seed=42
        )

        # Verify task_id is returned
        assert task_id is not None
        assert isinstance(task_id, str)

        # Get the published message
        call_args = mock_channel.basic_publish.call_args
        message_body = call_args[1]['body']
        message = json.loads(message_body)

        # Verify message format
        assert message['type'] == 'image_generation'
        assert message['data']['generation_id'] == 456
        assert message['data']['style_id'] == 123
        assert message['data']['lora_path'] == "/models/style_123/lora.safetensors"
        assert message['data']['prompt'] == "a beautiful sunset"
        assert message['data']['aspect_ratio'] == "1:1"
        assert message['data']['seed'] == 42

    @patch('app.services.rabbitmq_service.pika.BlockingConnection')
    def test_message_delivery_to_correct_queue(self, mock_connection):
        """Test that messages are sent to correct queues."""
        # Mock channel
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        mock_connection.return_value.is_closed = False

        # Send training task
        self.service.send_training_task(
            style_id=123,
            image_paths=["/path/to/image.jpg"],
            num_epochs=200
        )

        # Verify published to model_training queue
        call_args = mock_channel.basic_publish.call_args
        assert call_args[1]['routing_key'] == 'model_training'

        # Send generation task
        self.service.send_generation_task(
            generation_id=456,
            style_id=123,
            lora_path="/models/lora.safetensors",
            prompt="test prompt"
        )

        # Verify published to image_generation queue
        call_args = mock_channel.basic_publish.call_args
        assert call_args[1]['routing_key'] == 'image_generation'

    @patch('app.services.rabbitmq_service.pika.BlockingConnection')
    def test_connection_retry_logic(self, mock_connection):
        """Test that connection retry works correctly."""
        from pika.exceptions import AMQPConnectionError

        # Mock connection to fail 3 times (exceeding max_retries)
        mock_connection.side_effect = [
            AMQPConnectionError("Connection failed 1"),
            AMQPConnectionError("Connection failed 2"),
            AMQPConnectionError("Connection failed 3"),
        ]

        # This should raise after max retries (3)
        with pytest.raises(AMQPConnectionError):
            with self.service.get_channel() as channel:
                pass

        # Verify connection was attempted 3 times
        assert mock_connection.call_count == 3

    @patch('app.services.rabbitmq_service.pika.BlockingConnection')
    def test_no_connection_leak_after_multiple_messages(self, mock_connection):
        """Test that connections are properly managed after multiple messages."""
        # Mock channel
        mock_channel = MagicMock()
        mock_conn_instance = MagicMock()
        mock_conn_instance.channel.return_value = mock_channel
        mock_conn_instance.is_closed = False
        mock_connection.return_value = mock_conn_instance

        # Send 10 messages
        for i in range(10):
            self.service.send_training_task(
                style_id=i,
                image_paths=[f"/path/to/image{i}.jpg"],
                num_epochs=100
            )

        # Connection should be created only once (reused)
        assert mock_connection.call_count == 1

        # Close and verify
        self.service.close()
        assert mock_conn_instance.close.called or mock_channel.close.called

    def test_get_rabbitmq_service_singleton(self):
        """Test that get_rabbitmq_service returns singleton."""
        service1 = get_rabbitmq_service()
        service2 = get_rabbitmq_service()

        # Should be the same instance
        assert service1 is service2

    @patch('app.services.rabbitmq_service.pika.BlockingConnection')
    def test_webhook_url_generation(self, mock_connection):
        """Test that webhook URLs are generated correctly."""
        # Mock channel
        mock_channel = MagicMock()
        mock_connection.return_value.channel.return_value = mock_channel
        mock_connection.return_value.is_closed = False

        # Send task without webhook_url
        self.service.send_training_task(
            style_id=123,
            image_paths=["/path/to/image.jpg"],
            num_epochs=200
        )

        # Get message
        call_args = mock_channel.basic_publish.call_args
        message = json.loads(call_args[1]['body'])

        # Verify webhook_url was generated
        assert 'webhook_url' in message
        assert f"{settings.API_BASE_URL}/api/webhooks/training/123/status" == message['webhook_url']


print("RabbitMQ tests created successfully!")
