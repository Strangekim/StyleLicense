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
            logger.info(
                f"Connecting to RabbitMQ at {Config.RABBITMQ_HOST}:{Config.RABBITMQ_PORT}"
            )

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
            ch.basic_ack(
                delivery_tag=method.delivery_tag
            )  # Don't requeue invalid messages

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)

    def process_training_task(self, data: Dict[str, Any]) -> bool:
        """
        Process a training task

        Message format (from PATTERNS.md):
        {
          "data": {
            "style_id": 123,
            "images": ["gs://...", ...],
            "tags": ["watercolor", "portrait"],
            "parameters": {
              "epochs": 200,
              "learning_rate": 0.0001,
              "batch_size": 4
            }
          }
        }

        Args:
            data: Task data containing style_id, images, parameters

        Returns:
            True if successful, False otherwise
        """
        # Extract data from message format
        style_id = data.get("style_id")
        images = data.get("images", [])
        parameters = data.get("parameters", {})
        num_epochs = parameters.get("epochs", 200)
        learning_rate = parameters.get("learning_rate", 0.0001)

        if not style_id:
            logger.error("Missing style_id in task data")
            return False

        if not images:
            logger.error("Missing images in task data")
            return False

        logger.info(
            f"Processing training task: style_id={style_id}, images={len(images)}, epochs={num_epochs}, lr={learning_rate}"
        )

        try:
            # Mock training process (for Phase 1)
            # In Phase 2, this will be replaced with actual LoRA training
            success = self.mock_training(style_id, images, num_epochs)

            if success:
                # Generate mock model path
                model_path = f"gs://{Config.GCS_BUCKET_NAME}/models/style-{style_id}/lora_weights.safetensors"

                # Send training completed webhook
                WebhookService.send_training_completed(
                    style_id, model_path, loss=0.05, epochs=num_epochs
                )
                return True
            else:
                # Send training failed webhook
                WebhookService.send_training_failed(
                    style_id,
                    error_message="Mock training failed (simulated error)",
                    error_code="MOCK_TRAINING_ERROR",
                )
                return False

        except Exception as e:
            logger.error(f"Training task failed: {e}", exc_info=True)
            WebhookService.send_training_failed(
                style_id, error_message=str(e), error_code="INTERNAL_ERROR"
            )
            return False

    def mock_training(self, style_id: int, images: list, num_epochs: int) -> bool:
        """
        Mock training process (Phase 1 - Option 3 Hybrid approach)

        Simulates training by sleeping and sending progress updates.
        In Phase 2 (GCP GPU), this will be replaced with actual LoRA training.

        Args:
            style_id: Style model ID
            images: List of training image GCS paths
            num_epochs: Number of training epochs

        Returns:
            True if successful
        """
        logger.info(f"Starting mock training for style_id={style_id}")

        # Simulate downloading images (skip actual download for Phase 1)
        logger.info(f"Mock downloading {len(images)} images...")
        time.sleep(2)

        # Simulate training progress
        # In real training: num_epochs iterations
        # For mock: 10 steps representing the full training
        total_steps = 10
        step_duration = 3  # seconds per step
        last_progress_time = time.time()

        for step in range(1, total_steps + 1):
            # Calculate simulated epoch and progress
            current_epoch = int((step / total_steps) * num_epochs)
            progress_percent = int((step / total_steps) * 100)
            remaining_steps = total_steps - step
            estimated_seconds = remaining_steps * step_duration

            logger.info(
                f"Training progress: {progress_percent}% (epoch {current_epoch}/{num_epochs})"
            )

            # Send progress update (every 30 seconds in real training, but every step in mock)
            current_time = time.time()
            if (
                current_time - last_progress_time >= 5
                or step == 1
                or step == total_steps
            ):
                WebhookService.send_training_progress(
                    style_id=style_id,
                    current_epoch=current_epoch,
                    total_epochs=num_epochs,
                    progress_percent=progress_percent,
                    estimated_seconds=estimated_seconds,
                )
                last_progress_time = current_time

            # Sleep to simulate work
            time.sleep(step_duration)

        logger.info(f"Mock training completed for style_id={style_id}")
        return True
