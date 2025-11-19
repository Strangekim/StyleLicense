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
        Process a training task with retry logic

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

        # Retry logic: Max 3 attempts with exponential backoff
        max_attempts = 3
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Training attempt {attempt}/{max_attempts} for style_id={style_id}")

                # Phase 2: Real LoRA training with GPU
                model_path, final_loss = self.real_training(
                    style_id, images, num_epochs, learning_rate
                )

                if model_path:
                    # Send training completed webhook
                    WebhookService.send_training_completed(
                        style_id, model_path, loss=final_loss, epochs=num_epochs
                    )
                    return True
                else:
                    last_error = "Training failed - no model produced"
                    logger.warning(f"Attempt {attempt} failed: {last_error}")

            except Exception as e:
                last_error = str(e)
                logger.error(f"Training attempt {attempt} failed: {e}", exc_info=True)

            # Exponential backoff before retry (1s, 2s, 4s)
            if attempt < max_attempts:
                backoff_seconds = 2 ** (attempt - 1)
                logger.info(f"Retrying in {backoff_seconds} seconds...")
                time.sleep(backoff_seconds)

        # All attempts failed
        logger.error(f"All {max_attempts} training attempts failed for style_id={style_id}")
        WebhookService.send_training_failed(
            style_id,
            error_message=f"Training failed after {max_attempts} attempts: {last_error}",
            error_code="TRAINING_ERROR",
        )
        return False

    def real_training(
        self, style_id: int, images: list, num_epochs: int, learning_rate: float
    ) -> tuple:
        """
        Real LoRA training process (Phase 2 - GPU Implementation)

        Args:
            style_id: Style model ID
            images: List of training image GCS paths
            num_epochs: Number of training epochs
            learning_rate: Learning rate

        Returns:
            Tuple of (model_path, final_loss) if successful, (None, 0.0) otherwise
        """
        import os
        import tempfile
        from training.trainer import LoRATrainer

        logger.info(f"Starting real LoRA training for style_id={style_id}")
        logger.info(f"  Images: {len(images)}")
        logger.info(f"  Epochs: {num_epochs}")
        logger.info(f"  Learning rate: {learning_rate}")

        try:
            # Step 1: Download images from GCS
            logger.info("Downloading images from GCS...")
            with tempfile.TemporaryDirectory() as temp_dir:
                image_dir = os.path.join(temp_dir, "images")
                os.makedirs(image_dir, exist_ok=True)

                local_image_paths = self.gcs_service.download_images(images, image_dir)

                if not local_image_paths:
                    logger.error("Failed to download any images")
                    return (None, 0.0)

                logger.info(f"Downloaded {len(local_image_paths)} images")

                # Step 2: Setup training output directory
                output_dir = os.path.join(temp_dir, "output")
                os.makedirs(output_dir, exist_ok=True)

                # Step 3: Initialize trainer
                trainer = LoRATrainer(
                    style_id=style_id,
                    output_dir=output_dir,
                    num_epochs=num_epochs,
                    learning_rate=learning_rate,
                )

                # Step 4: Define progress callback
                def progress_callback(current_epoch, total_epochs, loss):
                    progress_percent = int((current_epoch / total_epochs) * 100)
                    remaining_epochs = total_epochs - current_epoch
                    estimated_seconds = remaining_epochs * 36  # Assume 36s/epoch

                    logger.info(
                        f"Training progress: {progress_percent}% (epoch {current_epoch}/{total_epochs}, loss={loss:.4f})"
                    )

                    WebhookService.send_training_progress(
                        style_id=style_id,
                        current_epoch=current_epoch,
                        total_epochs=total_epochs,
                        progress_percent=progress_percent,
                        estimated_seconds=estimated_seconds,
                    )

                # Step 5: Train model
                logger.info("Starting LoRA training...")
                model_dir = trainer.train(
                    image_paths=local_image_paths,
                    progress_callback=progress_callback,
                    progress_interval=30,  # Send progress every 30 seconds
                )

                logger.info(f"Training completed. Model saved to: {model_dir}")

                # Step 6: Upload model to GCS
                logger.info("Uploading model to GCS...")
                model_gcs_path = self.gcs_service.upload_model(model_dir, style_id)

                logger.info(f"Model uploaded successfully: {model_gcs_path}")

                # Return model path and final loss (estimated)
                return (model_gcs_path, 0.05)  # TODO: Return actual final loss from trainer

        except Exception as e:
            logger.error(f"Real training failed: {e}", exc_info=True)
            return (None, 0.0)

    def mock_training(self, style_id: int, images: list, num_epochs: int) -> bool:
        """
        Mock training process (Phase 1 - Option 3 Hybrid approach)

        Simulates training by sleeping and sending progress updates.
        Kept for backward compatibility and testing.

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
