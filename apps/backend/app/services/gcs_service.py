"""
GCS Service for uploading training images and models
"""
import os
from typing import BinaryIO
from django.conf import settings
from google.cloud import storage


class GCSService:
    """Service for uploading files to Google Cloud Storage"""

    def __init__(self):
        """Initialize GCS client"""
        self.client = None
        self.bucket = None

        try:
            # Use Application Default Credentials or credentials from environment
            if hasattr(settings, 'GOOGLE_APPLICATION_CREDENTIALS') and settings.GOOGLE_APPLICATION_CREDENTIALS:
                if os.path.exists(settings.GOOGLE_APPLICATION_CREDENTIALS):
                    self.client = storage.Client.from_service_account_json(
                        settings.GOOGLE_APPLICATION_CREDENTIALS
                    )
                else:
                    # Try ADC
                    self.client = storage.Client()
            else:
                # Use Application Default Credentials (works on Cloud Run)
                self.client = storage.Client()

            self.bucket = self.client.bucket(settings.GCS_BUCKET_NAME)

        except Exception as e:
            print(f"[WARNING] Failed to initialize GCS client: {e}")
            print("[WARNING] GCS functionality will be disabled")

    def upload_training_image(
        self, style_id: int, image_file: BinaryIO, image_index: int, filename: str
    ) -> str:
        """
        Upload a training image to GCS

        Args:
            style_id: Style model ID
            image_file: File object to upload
            image_index: Index of the image (0-based)
            filename: Original filename

        Returns:
            GCS URI (gs://bucket/path)

        Raises:
            RuntimeError: If upload fails
        """
        if not self.bucket:
            raise RuntimeError("GCS client not initialized")

        try:
            # Get file extension
            ext = os.path.splitext(filename)[1].lstrip(".")
            if not ext:
                ext = "jpg"

            # Construct blob path: training/{style_id}/image_{index}.{ext}
            blob_path = f"training/{style_id}/image_{image_index}.{ext}"

            blob = self.bucket.blob(blob_path)

            # Reset file pointer to beginning
            image_file.seek(0)

            # Upload file
            blob.upload_from_file(image_file, content_type=f"image/{ext}")

            # Return GCS URI
            gcs_uri = f"gs://{settings.GCS_BUCKET_NAME}/{blob_path}"

            return gcs_uri

        except Exception as e:
            raise RuntimeError(f"Failed to upload training image: {e}") from e

    def upload_model(self, style_id: int, model_file: BinaryIO, filename: str) -> str:
        """
        Upload a trained model to GCS

        Args:
            style_id: Style model ID
            model_file: File object to upload
            filename: Model filename

        Returns:
            GCS URI (gs://bucket/path)

        Raises:
            RuntimeError: If upload fails
        """
        if not self.bucket:
            raise RuntimeError("GCS client not initialized")

        try:
            # Construct blob path: models/style-{style_id}/{filename}
            blob_path = f"models/style-{style_id}/{filename}"

            blob = self.bucket.blob(blob_path)

            # Reset file pointer
            model_file.seek(0)

            # Upload file
            blob.upload_from_file(model_file)

            # Return GCS URI
            gcs_uri = f"gs://{settings.GCS_BUCKET_NAME}/{blob_path}"

            return gcs_uri

        except Exception as e:
            raise RuntimeError(f"Failed to upload model: {e}") from e


# Singleton instance
_gcs_service = None


def get_gcs_service() -> GCSService:
    """Get or create GCS service singleton"""
    global _gcs_service
    if _gcs_service is None:
        _gcs_service = GCSService()
    return _gcs_service
