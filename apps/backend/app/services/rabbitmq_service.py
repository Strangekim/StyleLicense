"""
RabbitMQ service for publishing tasks to AI servers.

This service handles message publishing to RabbitMQ queues for:
- Model training tasks (Backend → Training Server)
- Image generation tasks (Backend → Inference Server)
"""
import json
import uuid
import logging
from typing import Dict, Any, Optional, List
from contextlib import contextmanager

import pika
from django.conf import settings


logger = logging.getLogger(__name__)


class RabbitMQService:
    """
    RabbitMQ message publishing service with connection pooling.
    """

    def __init__(self):
        """Initialize RabbitMQ connection parameters."""
        self.connection_params = pika.ConnectionParameters(
            host=settings.RABBITMQ_HOST,
            port=settings.RABBITMQ_PORT,
            virtual_host=settings.RABBITMQ_VHOST,
            credentials=pika.PlainCredentials(
                settings.RABBITMQ_USER,
                settings.RABBITMQ_PASS
            ),
            heartbeat=600,  # 10 minutes
            blocked_connection_timeout=300,  # 5 minutes
        )
        self._connection = None
        self._channel = None

    @contextmanager
    def get_channel(self):
        """
        Context manager for getting a channel with automatic cleanup.
        Implements connection retry logic.
        """
        max_retries = 3
        retry_count = 0

        while retry_count < max_retries:
            try:
                if self._connection is None or self._connection.is_closed:
                    self._connection = pika.BlockingConnection(self.connection_params)
                    self._channel = self._connection.channel()
                    logger.info("Connected to RabbitMQ at %s:%s", settings.RABBITMQ_HOST, settings.RABBITMQ_PORT)

                yield self._channel
                break

            except (pika.exceptions.AMQPConnectionError, pika.exceptions.ChannelClosed) as e:
                retry_count += 1
                logger.warning("RabbitMQ connection attempt %d/%d failed: %s", retry_count, max_retries, str(e))

                # Close existing connections before retry
                self.close()

                if retry_count >= max_retries:
                    logger.error("Failed to connect to RabbitMQ after %d attempts", max_retries)
                    raise

    def close(self):
        """Close RabbitMQ connection gracefully."""
        try:
            if self._channel and not self._channel.is_closed:
                self._channel.close()
            if self._connection and not self._connection.is_closed:
                self._connection.close()
            logger.info("Closed RabbitMQ connection")
        except Exception as e:
            logger.error("Error closing RabbitMQ connection: %s", str(e))
        finally:
            self._channel = None
            self._connection = None

    def declare_queue(self, queue_name: str, durable: bool = True):
        """
        Declare a queue.

        Args:
            queue_name: Name of the queue
            durable: Whether the queue should survive broker restart
        """
        with self.get_channel() as channel:
            channel.queue_declare(queue=queue_name, durable=durable)
            logger.info("Declared queue: %s (durable=%s)", queue_name, durable)

    def publish_message(
        self,
        queue_name: str,
        message: Dict[str, Any],
        durable: bool = True
    ):
        """
        Publish a message to a queue.

        Args:
            queue_name: Target queue name
            message: Message payload (will be JSON serialized)
            durable: Whether message should be persisted to disk
        """
        with self.get_channel() as channel:
            # Declare queue (idempotent)
            channel.queue_declare(queue=queue_name, durable=durable)

            # Publish message
            channel.basic_publish(
                exchange='',
                routing_key=queue_name,
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2 if durable else 1,  # 2 = persistent
                    content_type='application/json'
                )
            )
            logger.info("Published message to queue '%s': task_id=%s", queue_name, message.get('task_id'))

    def send_training_task(
        self,
        style_id: int,
        image_paths: List[str],
        num_epochs: int = 200,
        webhook_url: Optional[str] = None
    ) -> str:
        """
        Send a model training task to the training server.

        Args:
            style_id: ID of the style model to train
            image_paths: List of image file paths or URLs
            num_epochs: Number of training epochs
            webhook_url: Optional callback URL for status updates

        Returns:
            Task ID (UUID)
        """
        task_id = str(uuid.uuid4())

        # Build callback URL if not provided
        if webhook_url is None:
            webhook_url = f"{settings.API_BASE_URL}/api/webhooks/training/{style_id}/status"

        message = {
            "task_id": task_id,
            "type": "model_training",
            "data": {
                "style_id": style_id,
                "image_paths": image_paths,
                "num_epochs": num_epochs,
            },
            "webhook_url": webhook_url,
        }

        self.publish_message("model_training", message)
        return task_id

    def send_generation_task(
        self,
        generation_id: int,
        style_id: int,
        lora_path: str,
        prompt: str,
        aspect_ratio: str = "1:1",
        seed: Optional[int] = None,
        webhook_url: Optional[str] = None
    ) -> str:
        """
        Send an image generation task to the inference server.

        Args:
            generation_id: ID of the generation record
            style_id: ID of the style model to use
            lora_path: Path to LoRA weights file
            prompt: Generation prompt
            aspect_ratio: Image aspect ratio (1:1, 2:2, or 1:2)
            seed: Random seed for reproducibility
            webhook_url: Optional callback URL for status updates

        Returns:
            Task ID (UUID)
        """
        task_id = str(uuid.uuid4())

        # Build callback URL if not provided
        if webhook_url is None:
            webhook_url = f"{settings.API_BASE_URL}/api/webhooks/generation/{generation_id}/status"

        message = {
            "task_id": task_id,
            "type": "image_generation",
            "data": {
                "generation_id": generation_id,
                "style_id": style_id,
                "lora_path": lora_path,
                "prompt": prompt,
                "aspect_ratio": aspect_ratio,
                "seed": seed,
            },
            "webhook_url": webhook_url,
        }

        self.publish_message("image_generation", message)
        return task_id

    def __del__(self):
        """Cleanup on deletion."""
        self.close()


# Singleton instance
_rabbitmq_service = None


def get_rabbitmq_service() -> RabbitMQService:
    """
    Get singleton RabbitMQ service instance.

    Returns:
        RabbitMQService instance
    """
    global _rabbitmq_service
    if _rabbitmq_service is None:
        _rabbitmq_service = RabbitMQService()
    return _rabbitmq_service
