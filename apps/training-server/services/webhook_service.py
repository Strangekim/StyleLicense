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
    def send_training_progress(
        style_id: int,
        current_epoch: int,
        total_epochs: int,
        progress_percent: int,
        estimated_seconds: int,
    ) -> bool:
        """
        Send training progress update

        API Spec: PATCH /api/webhooks/training/progress

        Args:
            style_id: Style model ID
            current_epoch: Current training epoch
            total_epochs: Total number of epochs
            progress_percent: Progress percentage (0-100)
            estimated_seconds: Estimated seconds remaining

        Returns:
            True if webhook was sent successfully, False otherwise
        """
        webhook_url = f"{Config.BACKEND_URL}/api/webhooks/training/progress"

        payload = {
            "style_id": style_id,
            "progress": {
                "current_epoch": current_epoch,
                "total_epochs": total_epochs,
                "progress_percent": progress_percent,
                "estimated_seconds": estimated_seconds,
            },
        }

        try:
            logger.info(
                f"Sending training progress: style_id={style_id}, epoch={current_epoch}/{total_epochs}, progress={progress_percent}%"
            )

            response = requests.patch(
                webhook_url,
                json=payload,
                headers=Config.get_webhook_headers(),
                timeout=10,
            )

            response.raise_for_status()

            logger.info(
                f"Progress webhook sent successfully: style_id={style_id}, status_code={response.status_code}"
            )
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send progress webhook: {e}")
            return False

    @staticmethod
    def send_training_completed(
        style_id: int,
        model_path: str,
        loss: Optional[float] = None,
        epochs: Optional[int] = None,
    ) -> bool:
        """
        Send training completed notification

        API Spec: POST /api/webhooks/training/complete

        Args:
            style_id: Style model ID
            model_path: Path to trained model (e.g., gs://bucket/style_10.safetensors)
            loss: Final training loss
            epochs: Number of epochs trained

        Returns:
            True if successful
        """
        webhook_url = f"{Config.BACKEND_URL}/api/webhooks/training/complete"

        payload = {
            "style_id": style_id,
            "model_path": model_path,
        }

        if loss is not None or epochs is not None:
            payload["training_metric"] = {}
            if loss is not None:
                payload["training_metric"]["loss"] = loss
            if epochs is not None:
                payload["training_metric"]["epochs"] = epochs

        try:
            logger.info(
                f"Sending training completed webhook: style_id={style_id}, model_path={model_path}"
            )

            response = requests.post(
                webhook_url,
                json=payload,
                headers=Config.get_webhook_headers(),
                timeout=10,
            )

            response.raise_for_status()

            logger.info(
                f"Training completed webhook sent successfully: style_id={style_id}, status_code={response.status_code}"
            )
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send training completed webhook: {e}")
            return False

    @staticmethod
    def send_training_failed(
        style_id: int, error_message: str, error_code: str = "TRAINING_FAILED"
    ) -> bool:
        """
        Send training failed notification

        API Spec: POST /api/webhooks/training/failed

        Args:
            style_id: Style model ID
            error_message: Error message
            error_code: Error code (e.g., LOW_QUALITY_DATA, OOM_ERROR)

        Returns:
            True if successful
        """
        webhook_url = f"{Config.BACKEND_URL}/api/webhooks/training/failed"

        payload = {
            "style_id": style_id,
            "error_message": error_message,
            "error_code": error_code,
        }

        try:
            logger.info(
                f"Sending training failed webhook: style_id={style_id}, error={error_message}"
            )

            response = requests.post(
                webhook_url,
                json=payload,
                headers=Config.get_webhook_headers(),
                timeout=10,
            )

            response.raise_for_status()

            logger.info(
                f"Training failed webhook sent successfully: style_id={style_id}, status_code={response.status_code}"
            )
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to send training failed webhook: {e}")
            return False
