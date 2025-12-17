"""
GCS Service

Handles downloading images from Google Cloud Storage.
"""

import os
import logging
from typing import List
from pathlib import Path
from PIL import Image
from config import Config

logger = logging.getLogger(__name__)


class GCSService:
    """Service for downloading images from GCS"""

    def __init__(self):
        """Initialize GCS client"""
        # Initialize GCS client (will use default credentials on GCE VM)
        self.client = None
        self.bucket = None

        try:
            from google.cloud import storage

            # On GCE VM, this will automatically use the VM's service account
            # No explicit credentials needed
            self.client = storage.Client(project=Config.GCS_PROJECT_ID)
            self.bucket = self.client.bucket(Config.GCS_BUCKET_NAME)
            logger.info(
                f"GCS client initialized for bucket: {Config.GCS_BUCKET_NAME}"
            )
        except Exception as e:
            logger.warning(f"Failed to initialize GCS client: {e}")
            logger.warning("GCS functionality will be disabled.")

    def download_image(self, gcs_path: str, local_path: str) -> bool:
        """
        Download a single image from GCS

        Args:
            gcs_path: GCS path (e.g., gs://bucket/path/to/image.jpg, https://storage.googleapis.com/bucket/path, or path/to/image.jpg)
            local_path: Local file path to save the image

        Returns:
            True if download was successful, False otherwise
        """
        try:
            # Handle different GCS path formats
            blob_path = gcs_path

            # Remove https://storage.googleapis.com/bucket/ prefix if present
            if blob_path.startswith("https://storage.googleapis.com/"):
                blob_path = blob_path.replace("https://storage.googleapis.com/", "")
                # Now blob_path is like: stylelicense-media/signatures/file.png
                # Remove bucket name
                if blob_path.startswith(f"{Config.GCS_BUCKET_NAME}/"):
                    blob_path = blob_path.replace(f"{Config.GCS_BUCKET_NAME}/", "", 1)

            # Remove gs://bucket/ prefix if present
            elif blob_path.startswith(f"gs://{Config.GCS_BUCKET_NAME}/"):
                blob_path = blob_path.replace(f"gs://{Config.GCS_BUCKET_NAME}/", "")

            # Remove gs:// prefix for other buckets
            elif blob_path.startswith("gs://"):
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

    def upload_file(self, local_path: str, gcs_path: str) -> str:
        """
        Upload a file to GCS

        Args:
            local_path: Local file path
            gcs_path: GCS destination path (e.g., models/style-1/lora_weights.safetensors)

        Returns:
            GCS URI (gs://bucket/path)

        Raises:
            RuntimeError: If upload fails
        """
        try:
            if not self.bucket:
                raise RuntimeError("GCS client not initialized")

            if not os.path.exists(local_path):
                raise FileNotFoundError(f"Local file not found: {local_path}")

            logger.info(f"Uploading file to GCS: {gcs_path}")

            blob = self.bucket.blob(gcs_path)
            blob.upload_from_filename(local_path)

            gcs_uri = f"gs://{Config.GCS_BUCKET_NAME}/{gcs_path}"
            logger.info(f"Successfully uploaded: {gcs_uri}")

            return gcs_uri

        except Exception as e:
            logger.error(f"Failed to upload file to GCS: {e}")
            raise RuntimeError(f"GCS upload failed") from e

    def upload_directory(self, local_dir: str, gcs_prefix: str) -> List[str]:
        """
        Upload all files in a directory to GCS

        Args:
            local_dir: Local directory path
            gcs_prefix: GCS destination prefix (e.g., models/style-1/)

        Returns:
            List of uploaded GCS URIs

        Raises:
            RuntimeError: If upload fails
        """
        try:
            if not os.path.exists(local_dir):
                raise FileNotFoundError(f"Local directory not found: {local_dir}")

            uploaded_uris = []

            for root, dirs, files in os.walk(local_dir):
                for filename in files:
                    local_path = os.path.join(root, filename)

                    # Calculate relative path
                    rel_path = os.path.relpath(local_path, local_dir)

                    # GCS path
                    gcs_path = os.path.join(gcs_prefix, rel_path).replace("\\", "/")

                    # Upload file
                    gcs_uri = self.upload_file(local_path, gcs_path)
                    uploaded_uris.append(gcs_uri)

            logger.info(f"Uploaded {len(uploaded_uris)} files from {local_dir}")
            return uploaded_uris

        except Exception as e:
            logger.error(f"Failed to upload directory to GCS: {e}")
            raise RuntimeError(f"GCS directory upload failed") from e

    def download_lora_weights(self, gcs_path: str, local_dir: str) -> str:
        """
        Download LoRA weights from GCS.

        Args:
            gcs_path: GCS path to LoRA directory or file
                     (e.g., gs://bucket/models/style-19/ or gs://bucket/models/style-19/adapter_model.safetensors)
            local_dir: Local directory to save LoRA weights

        Returns:
            Local directory path containing LoRA weights

        Raises:
            RuntimeError: If download fails
        """
        try:
            if not self.bucket:
                raise RuntimeError("GCS client not initialized")

            # Parse GCS path to get directory prefix
            blob_path = gcs_path

            # Remove https://storage.googleapis.com/bucket/ prefix if present
            if blob_path.startswith("https://storage.googleapis.com/"):
                blob_path = blob_path.replace("https://storage.googleapis.com/", "")
                if blob_path.startswith(f"{Config.GCS_BUCKET_NAME}/"):
                    blob_path = blob_path.replace(f"{Config.GCS_BUCKET_NAME}/", "", 1)

            # Remove gs://bucket/ prefix if present
            elif blob_path.startswith(f"gs://{Config.GCS_BUCKET_NAME}/"):
                blob_path = blob_path.replace(f"gs://{Config.GCS_BUCKET_NAME}/", "")

            # Remove gs:// prefix for other buckets
            elif blob_path.startswith("gs://"):
                parts = blob_path.replace("gs://", "").split("/", 1)
                if len(parts) > 1:
                    blob_path = parts[1]

            # Extract directory prefix (remove filename if present)
            if blob_path.endswith(('.safetensors', '.json', '.bin', '.pt', '.pth')):
                # It's a file path, get directory
                blob_prefix = "/".join(blob_path.split("/")[:-1])
            else:
                # It's already a directory
                blob_prefix = blob_path.rstrip("/")

            logger.info(f"Downloading LoRA weights from GCS prefix: {blob_prefix}")

            # Create local directory
            os.makedirs(local_dir, exist_ok=True)

            # List all blobs with this prefix
            blobs = list(self.bucket.list_blobs(prefix=blob_prefix))

            if not blobs:
                raise RuntimeError(f"No files found at GCS path: {blob_prefix}")

            downloaded_count = 0
            for blob in blobs:
                # Skip if it's a directory marker
                if blob.name.endswith('/'):
                    continue

                # Get filename relative to prefix
                relative_path = blob.name[len(blob_prefix):].lstrip('/')
                if not relative_path:
                    continue

                # Local file path
                local_file_path = os.path.join(local_dir, relative_path)

                # Create subdirectories if needed
                os.makedirs(os.path.dirname(local_file_path), exist_ok=True)

                # Download file
                logger.info(f"  Downloading: {blob.name}")
                blob.download_to_filename(local_file_path)
                downloaded_count += 1

            if downloaded_count == 0:
                raise RuntimeError(f"No files downloaded from {blob_prefix}")

            logger.info(f"Successfully downloaded {downloaded_count} LoRA files to {local_dir}")
            return local_dir

        except Exception as e:
            logger.error(f"Failed to download LoRA weights: {e}")
            raise RuntimeError(f"LoRA weights download failed") from e

    def upload_model(self, model_dir: str, style_id: int) -> str:
        """
        Upload trained LoRA model to GCS

        Args:
            model_dir: Local directory containing LoRA weights
            style_id: Style model ID

        Returns:
            GCS URI to the main model file

        Raises:
            RuntimeError: If upload fails
        """
        try:
            gcs_prefix = f"models/style-{style_id}"

            logger.info(f"Uploading model for style {style_id} to {gcs_prefix}")

            # Upload all files in model directory
            uploaded_uris = self.upload_directory(model_dir, gcs_prefix)

            # Return URI to the main model file (adapter_model.safetensors)
            main_model_path = f"{gcs_prefix}/adapter_model.safetensors"
            main_model_uri = f"gs://{Config.GCS_BUCKET_NAME}/{main_model_path}"

            if main_model_uri in uploaded_uris:
                logger.info(f"Model uploaded successfully: {main_model_uri}")
                return main_model_uri
            else:
                # If adapter_model.safetensors not found, return first uploaded file
                logger.warning(
                    f"adapter_model.safetensors not found, returning first uploaded file"
                )
                return uploaded_uris[0] if uploaded_uris else ""

        except Exception as e:
            logger.error(f"Failed to upload model: {e}")
            raise RuntimeError(f"Model upload failed for style {style_id}") from e
