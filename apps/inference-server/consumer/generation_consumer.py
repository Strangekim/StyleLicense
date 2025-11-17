"""
RabbitMQ Consumer for image generation tasks.

Receives generation requests from the image_generation queue and processes them.
"""
import json
import logging
import time
from typing import Dict, Any
import pika
from config import Config
from services.webhook_service import WebhookService

logger = logging.getLogger(__name__)


class GenerationConsumer:
    """RabbitMQ Consumer for image generation tasks."""

    def __init__(self):
        """Initialize generation consumer."""
        self.connection = None
        self.channel = None

    def connect(self):
        """Connect to RabbitMQ and declare queue."""
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

            # Declare queue (durable=True for persistence)
            self.channel.queue_declare(
                queue=Config.QUEUE_IMAGE_GENERATION, durable=True
            )

            # Set QoS to process one message at a time
            self.channel.basic_qos(prefetch_count=1)

            logger.info("Successfully connected to RabbitMQ")

        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def on_message(self, ch, method, properties, body):
        """
        Callback function for RabbitMQ messages.

        Args:
            ch: Channel
            method: Delivery method
            properties: Message properties
            body: Message body
        """
        try:
            # Parse message
            message = json.loads(body)
            logger.info(f"Received generation task: {message}")

            task_id = message.get("task_id")
            task_type = message.get("type")
            data = message.get("data", {})

            if task_type == "image_generation":
                success = self.process_generation_task(data)

                if success:
                    logger.info(f"Task {task_id} completed successfully")
                    ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    logger.error(f"Task {task_id} failed")
                    ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
            else:
                logger.warning(f"Unknown task type: {task_type}")
                ch.basic_ack(delivery_tag=method.delivery_tag)

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

        except Exception as e:
            logger.error(f"Error processing message: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    def process_generation_task(self, data: Dict[str, Any]) -> bool:
        """
        Process image generation task.

        Args:
            data: Task data containing generation_id, style_id, prompt, etc.

        Returns:
            bool: True if successful, False otherwise
        """
        generation_id = data.get("generation_id")
        style_id = data.get("style_id")
        prompt = data.get("prompt", "")
        lora_path = data.get("lora_path", "")
        num_steps = data.get("num_inference_steps", Config.INFERENCE_STEPS)

        try:
            logger.info(
                f"Processing generation task: generation_id={generation_id}, "
                f"style_id={style_id}, steps={num_steps}"
            )

            # Mock generation (for M1 phase - replace with actual inference in M4)
            success = self.mock_generation(generation_id, prompt, num_steps)

            return success

        except Exception as e:
            logger.error(f"Generation failed: {e}")
            WebhookService.send_inference_failed(
                generation_id, str(e), error_code="GENERATION_ERROR"
            )
            return False

    def mock_generation(
        self, generation_id: int, prompt: str, num_steps: int = 50
    ) -> bool:
        """
        Mock image generation process (for M1 phase).

        Simulates image generation with progress updates.
        Replace this with actual Stable Diffusion inference in M4.

        Args:
            generation_id: Generation ID
            prompt: Text prompt
            num_steps: Number of inference steps

        Returns:
            bool: True if successful
        """
        logger.info(f"Starting mock generation for generation_id={generation_id}")
        logger.info(f"Prompt: {prompt}")

        # Simulate generation with progress updates
        progress_milestones = [0, 25, 50, 75, 90, 100]
        total_duration = 10  # 10 seconds total

        for i, progress in enumerate(progress_milestones):
            current_step = int(num_steps * progress / 100)
            remaining_time = int(
                total_duration * (100 - progress) / 100
            )  # Estimate remaining time

            logger.info(f"Generation progress: {progress}%")
            WebhookService.send_inference_progress(
                generation_id=generation_id,
                current_step=current_step,
                total_steps=num_steps,
                progress_percent=progress,
                estimated_seconds=remaining_time,
            )

            if i < len(progress_milestones) - 1:
                # Sleep between progress updates
                time.sleep(total_duration / (len(progress_milestones) - 1))

        # Mock generated image URL
        mock_image_url = (
            f"gs://{Config.GCS_BUCKET_NAME}/generations/gen-{generation_id}.png"
        )

        # Send completion webhook
        WebhookService.send_inference_completed(
            generation_id=generation_id,
            result_url=mock_image_url,
            seed=42,
            steps=num_steps,
            guidance_scale=Config.GUIDANCE_SCALE,
        )

        logger.info(f"Mock generation completed for generation_id={generation_id}")
        return True

    def start_consuming(self):
        """Start consuming messages from queue."""
        try:
            logger.info(
                f"Waiting for messages on queue: {Config.QUEUE_IMAGE_GENERATION}"
            )

            self.channel.basic_consume(
                queue=Config.QUEUE_IMAGE_GENERATION,
                on_message_callback=self.on_message,
                auto_ack=False,
            )

            self.channel.start_consuming()

        except KeyboardInterrupt:
            logger.info("Stopping consumer...")
            self.stop()

        except Exception as e:
            logger.error(f"Error in consumer: {e}")
            raise

    def stop(self):
        """Stop consuming and close connection."""
        if self.channel:
            self.channel.stop_consuming()

        if self.connection and not self.connection.is_closed:
            self.connection.close()

        logger.info("Consumer stopped")
