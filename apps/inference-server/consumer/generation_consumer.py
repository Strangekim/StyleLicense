"""
RabbitMQ Consumer for image generation tasks.

Receives generation requests from the image_generation queue and processes them.
"""
import json
import logging
import time
from typing import Dict, Any
import pika
from PIL import Image
from config import Config
from services.webhook_service import WebhookService

logger = logging.getLogger(__name__)


class GenerationConsumer:
    """RabbitMQ Consumer for image generation tasks with batch processing support."""

    def __init__(self, prefetch_count: int = 10):
        """
        Initialize generation consumer.

        Args:
            prefetch_count: Number of messages to prefetch (default: 10 for batch processing)
        """
        self.connection = None
        self.channel = None
        self.prefetch_count = prefetch_count
        self.generator = None  # Reusable generator instance for efficiency
        self._current_lora_path = None  # Track loaded LoRA to avoid reloading

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

            # Set QoS for batch processing (prefetch multiple messages)
            self.channel.basic_qos(prefetch_count=self.prefetch_count)
            logger.info(f"Prefetch count set to {self.prefetch_count} for batch processing")

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
        Process image generation task with retry logic.

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
        aspect_ratio = data.get("aspect_ratio", "1:1")
        signature_path = data.get("signature_path", "")
        signature_config = data.get("signature_config", {})
        prompt_tags = data.get("prompt_tags", [])

        logger.info(
            f"Processing generation task: generation_id={generation_id}, "
            f"style_id={style_id}, steps={num_steps}"
        )

        # Retry logic: Max 3 attempts with exponential backoff
        max_attempts = 3
        last_error = None

        for attempt in range(1, max_attempts + 1):
            try:
                logger.info(f"Generation attempt {attempt}/{max_attempts} for generation_id={generation_id}")

                # Phase 2: Real inference with GPU
                image_url = self.real_generation(
                    generation_id=generation_id,
                    prompt=prompt,
                    lora_path=lora_path,
                    aspect_ratio=aspect_ratio,
                    num_steps=num_steps,
                    signature_path=signature_path,
                    signature_config=signature_config,
                    prompt_tags=prompt_tags,
                )

                if image_url:
                    return True
                else:
                    last_error = "Generation failed - no image produced"
                    logger.warning(f"Attempt {attempt} failed: {last_error}")

            except Exception as e:
                last_error = str(e)
                logger.error(f"Generation attempt {attempt} failed: {e}", exc_info=True)

            # Exponential backoff before retry (1s, 2s, 4s)
            if attempt < max_attempts:
                backoff_seconds = 2 ** (attempt - 1)
                logger.info(f"Retrying in {backoff_seconds} seconds...")
                time.sleep(backoff_seconds)

        # All attempts failed
        logger.error(f"All {max_attempts} generation attempts failed for generation_id={generation_id}")
        WebhookService.send_inference_failed(
            generation_id,
            f"Generation failed after {max_attempts} attempts: {last_error}",
            error_code="GENERATION_ERROR",
        )
        return False

    def real_generation(
        self,
        generation_id: int,
        prompt: str,
        lora_path: str,
        aspect_ratio: str = "1:1",
        num_steps: int = 50,
        signature_path: str = "",
        signature_config: dict = None,
        prompt_tags: list = None,
    ) -> str:
        """
        Real image generation process (Phase 2 - GPU Implementation).

        Args:
            generation_id: Generation ID
            prompt: Text prompt
            lora_path: Path to LoRA weights
            aspect_ratio: Aspect ratio (default: "1:1")
            num_steps: Number of inference steps (default: 50)
            signature_path: Path to signature image
            signature_config: Signature configuration (position, size, opacity)
            prompt_tags: List of prompt tags

        Returns:
            str: GCS URL of generated image, or None if failed
        """
        import os
        import tempfile
        from inference.generator import ImageGenerator
        from inference.watermark import WatermarkService
        from services.gcs_service import GCSService

        logger.info(f"Starting real generation for generation_id={generation_id}")
        logger.info(f"  Prompt: {prompt}")
        logger.info(f"  LoRA path: {lora_path}")
        logger.info(f"  Aspect ratio: {aspect_ratio}")

        signature_config = signature_config or {}
        gcs_service = GCSService()

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                # Step 1: Download LoRA weights from GCS if needed
                local_lora_path = None
                if lora_path:
                    # Check if it's a GCS path
                    if lora_path.startswith("gs://") or lora_path.startswith("https://storage.googleapis.com/"):
                        logger.info("Downloading LoRA weights from GCS...")
                        local_lora_path = os.path.join(temp_dir, "lora_weights")

                        try:
                            # Download LoRA weights from GCS
                            local_lora_path = gcs_service.download_lora_weights(lora_path, local_lora_path)
                            logger.info(f"LoRA weights downloaded to: {local_lora_path}")
                        except Exception as e:
                            logger.error(f"Failed to download LoRA weights from GCS: {e}")
                            local_lora_path = None

                    # Local path (for development/testing)
                    elif os.path.exists(lora_path):
                        logger.info(f"Using local LoRA weights: {lora_path}")
                        local_lora_path = lora_path

                    else:
                        logger.warning(f"LoRA weights path not found: {lora_path}")
                        local_lora_path = None

                # Step 2: Initialize or reuse generator for batch efficiency
                if self.generator is None:
                    logger.info("Initializing new ImageGenerator for batch processing")
                    self.generator = ImageGenerator()

                generator = self.generator

                # Step 3: Define progress callback
                def progress_callback(current_step, total_steps):
                    progress_percent = int((current_step / total_steps) * 100)
                    remaining_steps = total_steps - current_step
                    estimated_seconds = remaining_steps * 0.2  # Assume 0.2s per step

                    # Send progress at milestones
                    milestones = {0, 25, 50, 75, 90}
                    if progress_percent in milestones or current_step == 0:
                        logger.info(f"Generation progress: {progress_percent}%")
                        WebhookService.send_inference_progress(
                            generation_id=generation_id,
                            current_step=current_step,
                            total_steps=total_steps,
                            progress_percent=progress_percent,
                            estimated_seconds=int(estimated_seconds),
                        )

                # Step 4: Generate image
                logger.info("Generating image...")
                image = generator.generate(
                    prompt=prompt,
                    lora_weights_path=local_lora_path,
                    aspect_ratio=aspect_ratio,
                    num_inference_steps=num_steps,
                    progress_callback=progress_callback,
                )

                logger.info(f"Image generated: {image.size}")

                # Step 5: Insert signature if provided
                if signature_path:
                    logger.info(f"Artist signature provided: {signature_path}")

                    # Download signature from GCS if it's a GCS URI
                    local_signature_path = None
                    if signature_path.startswith("gs://") or signature_path.startswith("https://storage.googleapis.com/"):
                        logger.info("Downloading signature from GCS...")
                        local_signature_path = os.path.join(temp_dir, "signature.png")
                        if gcs_service.download_image(signature_path, local_signature_path):
                            logger.info("Signature downloaded successfully")
                        else:
                            logger.warning("Failed to download signature from GCS")
                            local_signature_path = None
                    elif os.path.exists(signature_path):
                        # Local file path (for testing)
                        local_signature_path = signature_path
                    else:
                        logger.warning(f"Signature path not found: {signature_path}")

                    # Insert signature if we have a valid local file
                    if local_signature_path and os.path.exists(local_signature_path):
                        logger.info("Inserting artist signature...")
                        watermark_service = WatermarkService()

                        signature_image = Image.open(local_signature_path)

                        image = watermark_service.insert_signature(
                            image=image,
                            signature_image=signature_image,
                            position=signature_config.get("position", "bottom-right"),
                            size=signature_config.get("size", "medium"),
                            opacity=signature_config.get("opacity", 0.7),
                        )

                        logger.info("Signature inserted successfully")
                    else:
                        logger.warning("Skipping signature insertion - signature file not available")

                # Step 6: Save image locally
                output_path = os.path.join(temp_dir, f"gen-{generation_id}.png")
                image.save(output_path, "PNG")

                logger.info(f"Image saved locally: {output_path}")

                # Step 7: Upload to GCS
                logger.info("Uploading image to GCS...")
                gcs_path = f"generations/gen-{generation_id}.png"
                image_url = gcs_service.upload_file(output_path, gcs_path)

                logger.info(f"Image uploaded: {image_url}")

                # Step 8: Send completion webhook
                WebhookService.send_inference_completed(
                    generation_id=generation_id,
                    result_url=image_url,
                    seed=None,  # TODO: Return actual seed from generator
                    steps=num_steps,
                    guidance_scale=Config.GUIDANCE_SCALE,
                    prompt_tags=prompt_tags or [],
                )

                logger.info(f"Real generation completed for generation_id={generation_id}")

                # Note: Pipeline is kept loaded for batch processing efficiency
                # Call cleanup_generator() when done with all generations

                return image_url

        except Exception as e:
            logger.error(f"Real generation failed: {e}", exc_info=True)
            WebhookService.send_inference_failed(
                generation_id, str(e), error_code="INFERENCE_ERROR"
            )
            return None

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

    def cleanup_generator(self):
        """Cleanup generator to free GPU memory."""
        if self.generator:
            self.generator.unload_pipeline()
            self.generator = None
            self._current_lora_path = None
            logger.info("Generator cleaned up, GPU memory freed")

    def stop(self):
        """Stop consuming, cleanup resources, and close connection."""
        # Cleanup generator to free GPU memory
        self.cleanup_generator()

        if self.channel:
            self.channel.stop_consuming()

        if self.connection and not self.connection.is_closed:
            self.connection.close()

        logger.info("Consumer stopped")
