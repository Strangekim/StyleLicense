"""
GCS Service

Handles downloading images from Google Cloud Storage.
"""

import os
from typing import List
from pathlib import Path
from PIL import Image
from config import Config
from utils.logger import logger


class GCSService:
    """Service for downloading images from GCS"""

    def __init__(self):
        """Initialize GCS client"""
        # Only import and initialize GCS client if credentials are available
        self.client = None
        self.bucket = None

        if Config.GOOGLE_APPLICATION_CREDENTIALS and os.path.exists(
            Config.GOOGLE_APPLICATION_CREDENTIALS
        ):
            try:
                from google.cloud import storage

                self.client = storage.Client(project=Config.GCS_PROJECT_ID)
                self.bucket = self.client.bucket(Config.GCS_BUCKET_NAME)
                logger.info(
                    f"GCS client initialized for bucket: {Config.GCS_BUCKET_NAME}"
                )
            except Exception as e:
                logger.warning(f"Failed to initialize GCS client: {e}")
        else:
            logger.warning(
                "GCS credentials not found. GCS functionality will be disabled."
            )

    def download_image(self, gcs_path: str, local_path: str) -> bool:
        """
        Download a single image from GCS

        Args:
            gcs_path: GCS path (e.g., gs://bucket/path/to/image.jpg or path/to/image.jpg)
            local_path: Local file path to save the image

        Returns:
            True if download was successful, False otherwise
        """
        try:
            # Remove gs:// prefix and bucket name if present
            blob_path = gcs_path.replace(f"gs://{Config.GCS_BUCKET_NAME}/", "")
            blob_path = blob_path.replace("gs://", "").split("/", 1)[-1]

            logger.info(f"Downloading image from GCS: {blob_path}")

            if not self.bucket:
                logger.error("GCS client not initialized")
                return False

            blob = self.bucket.blob(blob_path)

            # Create parent directory if needed
            os.makedirs(os.path.dirname(local_path), exist_ok=True)

            blob.download_to_filename(local_path)

            # Validate downloaded image
            if self.validate_image(local_path):
                logger.info(f"Successfully downloaded: {local_path}")
                return True
            else:
                logger.error(f"Downloaded file is not a valid image: {local_path}")
                os.remove(local_path)
                return False

        except Exception as e:
            logger.error(f"Failed to download image from GCS: {e}")
            return False

    def download_images(self, gcs_paths: List[str], local_dir: str) -> List[str]:
        """
        Download multiple images from GCS

        Args:
            gcs_paths: List of GCS paths
            local_dir: Local directory to save images

        Returns:
            List of successfully downloaded local file paths
        """
        local_paths = []

        for i, gcs_path in enumerate(gcs_paths):
            # Extract filename from GCS path
            filename = Path(gcs_path).name

            # Generate local path
            local_path = os.path.join(local_dir, f"{i:04d}_{filename}")

            if self.download_image(gcs_path, local_path):
                local_paths.append(local_path)
            else:
                logger.warning(f"Skipping failed download: {gcs_path}")

        logger.info(
            f"Downloaded {len(local_paths)}/{len(gcs_paths)} images successfully"
        )

        return local_paths

    @staticmethod
    def validate_image(image_path: str) -> bool:
        """
        Validate that a file is a valid image

        Args:
            image_path: Path to image file

        Returns:
            True if valid image, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                img.verify()

            # Re-open to check if we can load the image data
            with Image.open(image_path) as img:
                img.load()

            return True
        except Exception as e:
            logger.error(f"Image validation failed for {image_path}: {e}")
            return False

    @staticmethod
    def validate_images(image_paths: List[str]) -> bool:
        """
        Validate multiple images

        Args:
            image_paths: List of image paths

        Returns:
            True if all images are valid, False otherwise
        """
        for path in image_paths:
            if not GCSService.validate_image(path):
                return False
        return True
