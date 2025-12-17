"""
Webhook Service

Sends callbacks to Backend API for generation progress/completion updates.
"""

import logging
from typing import Optional, Dict, Any
import requests
from config import Config

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhook callbacks to backend"""

    @staticmethod
    def send_inference_progress(
        generation_id: int,
        current_step: int,
        total_steps: int,
        progress_percent: int,
        estimated_seconds: int,
    ) -> bool:
        """
        Send inference progress update

        API Spec: PATCH /api/webhooks/inference/progress

        Args:
            generation_id: Generation ID
            current_step: Current inference step
            total_steps: Total number of steps
            progress_percent: Progress percentage (0-100)
            estimated_seconds: Estimated seconds remaining

        Returns:
            True if webhook was sent successfully, False otherwise
        """
        webhook_url = f"{Config.BACKEND_URL}/api/webhooks/inference/progress"

        payload = {
            "generation_id": generation_id,
            "progress": {
                "current_step": current_step,
                "total_steps": total_steps,
                "progress_percent": progress_percent,
                "estimated_seconds": estimated_seconds,
            },
        }

        try:
            logger.info(
                f"Sending inference progress: generation_id={generation_id}, "
                f"step={current_step}/{total_steps}, progress={progress_percent}%"
            )

            response = requests.patch(
                webhook_url,
                json=payload,
                headers=Config.get_webhook_headers(),
                timeout=10,
            )

            response.raise_for_status()

            logger.info(
                f"Progress webhook sent successfully: generation_id={generation_id}, "
                f"status_code={response.status_code}"
            )
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send progress webhook: {e}")
            return False

    @staticmethod
    def send_inference_completed(
        generation_id: int,
        result_url: str,
        seed: Optional[int] = None,
        steps: Optional[int] = None,
        guidance_scale: Optional[float] = None,
        prompt_tags: Optional[list] = None,
    ) -> bool:
        """
        Send inference completed notification

        API Spec: POST /api/webhooks/inference/complete

        Args:
            generation_id: Generation ID
            result_url: URL of generated image (e.g., gs://bucket/image.jpg)
            seed: Random seed used
            steps: Number of inference steps
            guidance_scale: CFG scale value
            prompt_tags: List of prompt tags

        Returns:
            True if successful
        """
        webhook_url = f"{Config.BACKEND_URL}/api/webhooks/inference/complete"

        payload = {
            "generation_id": generation_id,
            "result_url": result_url,
        }

        # Add metadata if provided
        metadata = {}
        if seed is not None:
            metadata["seed"] = seed
        if steps is not None:
            metadata["steps"] = steps
        if guidance_scale is not None:
            metadata["guidance_scale"] = guidance_scale
        if prompt_tags is not None:
            metadata["prompt_tags"] = prompt_tags

        if metadata:
            payload["metadata"] = metadata

        try:
            logger.info(
                f"Sending inference completed webhook: generation_id={generation_id}, "
                f"result_url={result_url}"
            )

            response = requests.post(
                webhook_url,
                json=payload,
                headers=Config.get_webhook_headers(),
                timeout=10,
            )

            response.raise_for_status()

            logger.info(
                f"Inference completed webhook sent successfully: generation_id={generation_id}, "
                f"status_code={response.status_code}"
            )
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send inference completed webhook: {e}")
            return False

    @staticmethod
    def send_inference_failed(
        generation_id: int, error_message: str, error_code: str = "GENERATION_FAILED"
    ) -> bool:
        """
        Send inference failed notification

        API Spec: POST /api/webhooks/inference/failed

        Args:
            generation_id: Generation ID
            error_message: Error message
            error_code: Error code (e.g., OOM_ERROR, INVALID_PROMPT)

        Returns:
            True if successful
        """
        webhook_url = f"{Config.BACKEND_URL}/api/webhooks/inference/failed"

        payload = {
            "generation_id": generation_id,
            "error_message": error_message,
            "error_code": error_code,
        }

        try:
            logger.info(
                f"Sending inference failed webhook: generation_id={generation_id}, "
                f"error={error_message}"
            )

            response = requests.post(
                webhook_url,
                json=payload,
                headers=Config.get_webhook_headers(),
                timeout=10,
            )

            response.raise_for_status()

            logger.info(
                f"Inference failed webhook sent successfully: generation_id={generation_id}, "
                f"status_code={response.status_code}"
            )
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send inference failed webhook: {e}")
            return False
