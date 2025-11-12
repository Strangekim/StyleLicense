"""
Training Consumer

RabbitMQ consumer for processing training tasks.
"""

import json
import time
import pika
from typing import Dict, Any
from config import Config
from utils.logger import logger
from services.webhook_service import WebhookService
from services.gcs_service import GCSService


class TrainingConsumer:
    """RabbitMQ consumer for model training tasks"""

    def __init__(self):
        """Initialize consumer"""
        self.connection = None
        self.channel = None
        self.gcs_service = GCSService()

    def connect(self):
        """Establish connection to RabbitMQ"""
        try:
            logger.info(f"Connecting to RabbitMQ at {Config.RABBITMQ_HOST}:{Config.RABBITMQ_PORT}")

            credentials = pika.PlainCredentials(
                Config.RABBITMQ_USER, Config.RABBITMQ_PASSWORD
            )

            parameters = pika.ConnectionParameters(
                host=Config.RABBITMQ_HOST,
                port=Config.RABBITMQ_PORT,
                virtual_host=Config.RABBITMQ_VHOST,
                credentials=credentials,
                heartbeat=600,
                blocked_connection_timeout=300,
            )

            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declare queue
            self.channel.queue_declare(queue=Config.TRAINING_QUEUE, durable=True)

            # Set QoS
            self.channel.basic_qos(prefetch_count=1)

            logger.info("Successfully connected to RabbitMQ")
            return True

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            return False

    def start_consuming(self):
        """Start consuming messages from queue"""
        if not self.channel:
            if not self.connect():
                raise RuntimeError("Failed to connect to RabbitMQ")

        logger.info(f"Waiting for messages on queue: {Config.TRAINING_QUEUE}")

        self.channel.basic_consume(
            queue=Config.TRAINING_QUEUE,
            on_message_callback=self.on_message,
            auto_ack=False,
        )

        try:
            self.channel.start_consuming()
        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.stop_consuming()

    def stop_consuming(self):
        """Stop consuming and close connection"""
        if self.channel:
            self.channel.stop_consuming()

        if self.connection:
            self.connection.close()

        logger.info("Consumer stopped")

    def on_message(self, ch, method, properties, body):
        """
        Callback for processing messages

        Args:
            ch: Channel
            method: Method
            properties: Properties
            body: Message body
        """
        try:
            # Parse message
            message = json.loads(body)
            logger.info(f"Received training task: {message}")

            # Extract task data
            task_id = message.get("task_id")
            task_type = message.get("type")
            data = message.get("data", {})

            if task_type != "model_training":
                logger.warning(f"Unknown task type: {task_type}")
                ch.basic_ack(delivery_tag=method.delivery_tag)
                return

            # Process training task
            success = self.process_training_task(data)

            if success:
                # Acknowledge message
                ch.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Task {task_id} completed successfully")
            else:
                # Reject and requeue
                ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
                logger.error(f"Task {task_id} failed, requeuing")

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            ch.basic_ack(delivery_tag=method.delivery_tag)  # Don't requeue invalid messages

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def process_training_task(self, data: Dict[str, Any]) -> bool:
        """
        Process a training task

        Args:
            data: Task data containing style_id, image_paths, num_epochs

        Returns:
            True if successful, False otherwise
        """
        style_id = data.get("style_id")
        image_paths = data.get("image_paths", [])
        num_epochs = data.get("num_epochs", 200)

        if not style_id:
            logger.error("Missing style_id in task data")
            return False

        if not image_paths:
            logger.error("Missing image_paths in task data")
            return False

        logger.info(
            f"Processing training task: style_id={style_id}, images={len(image_paths)}, epochs={num_epochs}"
        )

        try:
            # Send training started webhook
            WebhookService.send_training_started(style_id)

            # Mock training process (for M1 phase)
            # In M4, this will be replaced with actual LoRA training
            success = self.mock_training(style_id, image_paths, num_epochs)

            if success:
                # Generate mock model path
                model_path = f"gs://{Config.GCS_BUCKET_NAME}/models/style-{style_id}/lora_weights.safetensors"

                # Send training completed webhook
                WebhookService.send_training_completed(style_id, model_path)
                return True
            else:
                # Send training failed webhook
                WebhookService.send_training_failed(
                    style_id, "Mock training failed (simulated error)"
                )
                return False

        except Exception as e:
            logger.error(f"Training task failed: {e}", exc_info=True)
            WebhookService.send_training_failed(style_id, str(e))
            return False

    def mock_training(self, style_id: int, image_paths: list, num_epochs: int) -> bool:
        """
        Mock training process (for M1 phase)

        Simulates training by sleeping and sending progress updates.
        In M4, this will be replaced with actual LoRA training.

        Args:
            style_id: Style model ID
            image_paths: List of training image paths
            num_epochs: Number of training epochs

        Returns:
            True if successful
        """
        logger.info(f"Starting mock training for style_id={style_id}")

        # Simulate downloading images (skip actual download for M1)
        logger.info(f"Mock downloading {len(image_paths)} images...")
        time.sleep(2)

        # Simulate training progress
        total_steps = 10
        step_duration = 3  # seconds per step

        for step in range(1, total_steps + 1):
            progress = int((step / total_steps) * 100)
            logger.info(f"Training progress: {progress}%")

            # Send progress update
            WebhookService.send_training_progress(style_id, progress)

            # Sleep to simulate work
            time.sleep(step_duration)

        logger.info(f"Mock training completed for style_id={style_id}")
        return True
