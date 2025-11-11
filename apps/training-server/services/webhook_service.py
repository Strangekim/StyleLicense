"""
Webhook Service

Handles sending status updates to the backend via webhooks.
"""

import requests
from typing import Dict, Any, Optional
from config import Config
from utils.logger import logger


class WebhookService:
    """Service for sending webhook callbacks to backend"""

    @staticmethod
    def send_training_status(
        style_id: int,
        status: str,
        progress: Optional[int] = None,
        model_path: Optional[str] = None,
        failure_reason: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """
        Send training status update to backend

        Args:
            style_id: Style model ID
            status: Training status (processing, completed, failed)
            progress: Training progress percentage (0-100)
            model_path: Path to trained model (for completed status)
            failure_reason: Error message (for failed status)
            metadata: Additional metadata

        Returns:
            True if webhook was sent successfully, False otherwise
        """
        webhook_url = f"{Config.BACKEND_URL}/api/webhooks/training/{style_id}/status"

        payload = {
            "training_status": status,
        }

        if progress is not None:
            payload["progress"] = progress

        if model_path:
            payload["model_path"] = model_path

        if failure_reason:
            payload["failure_reason"] = failure_reason

        if metadata:
            payload["metadata"] = metadata

        try:
            logger.info(
                f"Sending training status update: style_id={style_id}, status={status}, progress={progress}"
            )

            response = requests.patch(
                webhook_url,
                json=payload,
                headers=Config.get_webhook_headers(),
                timeout=10,
            )

            response.raise_for_status()

            logger.info(
                f"Webhook sent successfully: style_id={style_id}, status_code={response.status_code}"
            )
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send webhook: {e}")
            return False

    @staticmethod
    def send_training_started(style_id: int) -> bool:
        """
        Send training started notification

        Args:
            style_id: Style model ID

        Returns:
            True if successful
        """
        return WebhookService.send_training_status(
            style_id=style_id, status="processing", progress=0
        )

    @staticmethod
    def send_training_progress(style_id: int, progress: int) -> bool:
        """
        Send training progress update

        Args:
            style_id: Style model ID
            progress: Progress percentage (0-100)

        Returns:
            True if successful
        """
        return WebhookService.send_training_status(
            style_id=style_id, status="processing", progress=progress
        )

    @staticmethod
    def send_training_completed(style_id: int, model_path: str) -> bool:
        """
        Send training completed notification

        Args:
            style_id: Style model ID
            model_path: Path to trained model

        Returns:
            True if successful
        """
        return WebhookService.send_training_status(
            style_id=style_id, status="completed", progress=100, model_path=model_path
        )

    @staticmethod
    def send_training_failed(style_id: int, failure_reason: str) -> bool:
        """
        Send training failed notification

        Args:
            style_id: Style model ID
            failure_reason: Error message

        Returns:
            True if successful
        """
        return WebhookService.send_training_status(
            style_id=style_id, status="failed", failure_reason=failure_reason
        )
