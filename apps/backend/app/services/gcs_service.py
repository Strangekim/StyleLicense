"""
GCS Service for file uploads

Handles uploading files to Google Cloud Storage.
"""
import logging
from typing import BinaryIO
from django.conf import settings

logger = logging.getLogger(__name__)


class GCSService:
    """Service for uploading files to Google Cloud Storage"""

    def __init__(self):
        """Initialize GCS client"""
        try:
            from google.cloud import storage
            self.client = storage.Client()
            self.bucket = self.client.bucket(settings.GCS_BUCKET_NAME)
            logger.info(f"GCS client initialized for bucket: {settings.GCS_BUCKET_NAME}")
        except Exception as e:
            logger.warning(f"Failed to initialize GCS client: {e}")
            self.client = None
            self.bucket = None

    def upload_training_image(
        self, style_id: int, image_file: BinaryIO, image_index: int, filename: str
    ) -> str:
        """
        Upload a training image to GCS

        Args:
            style_id: Style model ID
            image_file: File object to upload
            image_index: Index of the image (0-9)
            filename: Original filename

        Returns:
            GCS URI (gs://bucket/path)

        Raises:
            RuntimeError: If upload fails
        """
        if not self.bucket:
            raise RuntimeError("GCS client not initialized")

        try:
            # Determine file extension
            ext = filename.split('.')[-1] if '.' in filename else 'jpg'

            # GCS path: training/{style_id}/image_{index}.{ext}
            blob_path = f"training/{style_id}/image_{image_index}.{ext}"

            logger.info(f"Uploading training image to GCS: {blob_path}")

            # Create blob and upload
            blob = self.bucket.blob(blob_path)

            # Reset file pointer to beginning
            image_file.seek(0)

            # Upload file
            blob.upload_from_file(image_file, content_type=f"image/{ext}")

            # Construct GCS URI
            gcs_uri = f"gs://{settings.GCS_BUCKET_NAME}/{blob_path}"

            logger.info(f"Successfully uploaded: {gcs_uri}")
            return gcs_uri

        except Exception as e:
            logger.error(f"Failed to upload image to GCS: {e}", exc_info=True)
            raise RuntimeError(f"GCS upload failed: {e}") from e


# Singleton instance
_gcs_service = None


def get_gcs_service() -> GCSService:
    """
    Get singleton GCS service instance

    Returns:
        GCSService instance
    """
    global _gcs_service
    if _gcs_service is None:
        _gcs_service = GCSService()
    return _gcs_service
