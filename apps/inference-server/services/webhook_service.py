"""
Webhook Service for sending generation status updates to Backend API.
"""
import logging
from typing import Optional, Dict, Any
import requests
from config import Config

logger = logging.getLogger(__name__)


class WebhookService:
    """Service for sending webhooks to backend API."""

    @staticmethod
    def send_generation_status(
        generation_id: int,
        status: str,
        progress: Optional[int] = None,
        image_url: Optional[str] = None,
        failure_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send generation status update to backend.

        Args:
            generation_id: Generation ID
            status: Status (queued, processing, completed, failed)
            progress: Progress percentage (0-100)
            image_url: URL of generated image (for completed status)
            failure_reason: Error message (for failed status)
            metadata: Additional metadata (seed, steps, etc.)

        Returns:
            bool: True if webhook sent successfully, False otherwise
        """
        webhook_url = f"{Config.BACKEND_URL}/api/webhooks/generation/{generation_id}/status"

        payload = {"generation_status": status}

        if progress is not None:
            payload["progress"] = progress

        if image_url:
            payload["image_url"] = image_url

        if failure_reason:
            payload["failure_reason"] = failure_reason

        if metadata:
            payload["metadata"] = metadata

        try:
            logger.info(
                f"Sending generation status update: generation_id={generation_id}, "
                f"status={status}, progress={progress}"
            )

            response = requests.patch(
                webhook_url,
                json=payload,
                headers=Config.get_webhook_headers(),
                timeout=10,
            )
            response.raise_for_status()

            logger.info(f"Webhook sent successfully: {webhook_url}")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send webhook: {e}")
            return False

    @staticmethod
    def send_generation_started(generation_id: int) -> bool:
        """
        Send generation started notification.

        Args:
            generation_id: Generation ID

        Returns:
            bool: True if webhook sent successfully
        """
        return WebhookService.send_generation_status(
            generation_id=generation_id, status="processing", progress=0
        )

    @staticmethod
    def send_generation_progress(generation_id: int, progress: int) -> bool:
        """
        Send generation progress update.

        Args:
            generation_id: Generation ID
            progress: Progress percentage (0-100)

        Returns:
            bool: True if webhook sent successfully
        """
        return WebhookService.send_generation_status(
            generation_id=generation_id, status="processing", progress=progress
        )

    @staticmethod
    def send_generation_completed(
        generation_id: int, image_url: str, metadata: Optional[Dict[str, Any]] = None
    ) -> bool:
        """
        Send generation completed notification.

        Args:
            generation_id: Generation ID
            image_url: URL of generated image
            metadata: Additional metadata (seed, steps, etc.)

        Returns:
            bool: True if webhook sent successfully
        """
        return WebhookService.send_generation_status(
            generation_id=generation_id,
            status="completed",
            progress=100,
            image_url=image_url,
            metadata=metadata or {},
        )

    @staticmethod
    def send_generation_failed(generation_id: int, failure_reason: str) -> bool:
        """
        Send generation failed notification.

        Args:
            generation_id: Generation ID
            failure_reason: Error message

        Returns:
            bool: True if webhook sent successfully
        """
        return WebhookService.send_generation_status(
            generation_id=generation_id, status="failed", failure_reason=failure_reason
        )
