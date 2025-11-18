"""Image preprocessing and dataset preparation for LoRA training."""

import os
import logging
from pathlib import Path
from typing import List, Tuple
from PIL import Image
import torch
from torch.utils.data import Dataset
from torchvision import transforms

logger = logging.getLogger(__name__)


class StyleImageDataset(Dataset):
    """
    Dataset for style model training images.

    Handles image loading, preprocessing, and validation.
    Images are resized to 512x512, converted to RGB, and normalized.
    """

    def __init__(
        self,
        image_paths: List[str],
        target_size: int = 512,
        normalize: bool = True
    ):
        """
        Initialize dataset.

        Args:
            image_paths: List of local file paths to training images
            target_size: Target resolution (default: 512)
            normalize: Whether to normalize images to [-1, 1] (default: True)

        Raises:
            ValueError: If image_paths is empty or contains invalid paths
        """
        if not image_paths:
            raise ValueError("image_paths cannot be empty")

        self.image_paths = image_paths
        self.target_size = target_size
        self.normalize = normalize

        # Validate all images exist and are valid
        self.valid_paths = []
        for path in image_paths:
            if self._validate_image(path):
                self.valid_paths.append(path)
            else:
                logger.warning(f"Skipping invalid image: {path}")

        if not self.valid_paths:
            raise ValueError("No valid images found in image_paths")

        logger.info(f"Dataset initialized with {len(self.valid_paths)}/{len(image_paths)} valid images")

        # Define transforms
        transform_list = [
            transforms.Resize((target_size, target_size), interpolation=transforms.InterpolationMode.LANCZOS),
            transforms.ToTensor(),
        ]

        if normalize:
            # Normalize to [-1, 1] as expected by Stable Diffusion
            transform_list.append(transforms.Normalize([0.5], [0.5]))

        self.transform = transforms.Compose(transform_list)

    def _validate_image(self, path: str) -> bool:
        """
        Validate that image file exists and can be opened.

        Args:
            path: Path to image file

        Returns:
            True if valid, False otherwise
        """
        try:
            if not os.path.exists(path):
                return False

            # Try to open image
            with Image.open(path) as img:
                img.verify()

            # Re-open for actual loading (verify() closes the file)
            with Image.open(path) as img:
                # Check minimum size
                if img.width < 256 or img.height < 256:
                    logger.warning(f"Image {path} is too small: {img.size}")
                    return False

                # Check format
                if img.format not in ['JPEG', 'PNG', 'JPG']:
                    logger.warning(f"Image {path} has unsupported format: {img.format}")
                    return False

            return True

        except Exception as e:
            logger.error(f"Error validating image {path}: {e}")
            return False

    def __len__(self) -> int:
        """Return number of valid images."""
        return len(self.valid_paths)

    def __getitem__(self, idx: int) -> Tuple[torch.Tensor, str]:
        """
        Get preprocessed image.

        Args:
            idx: Index of image

        Returns:
            Tuple of (preprocessed image tensor, original path)
        """
        path = self.valid_paths[idx]

        try:
            # Load and convert to RGB
            image = Image.open(path).convert("RGB")

            # Apply transforms
            image_tensor = self.transform(image)

            return image_tensor, path

        except Exception as e:
            logger.error(f"Error loading image {path}: {e}")
            # Return a blank tensor on error
            if self.normalize:
                return torch.zeros((3, self.target_size, self.target_size)), path
            else:
                return torch.zeros((3, self.target_size, self.target_size)), path


def preprocess_images(
    image_paths: List[str],
    target_size: int = 512
) -> List[Image.Image]:
    """
    Preprocess training images (resize, normalize).

    This is a simpler alternative to StyleImageDataset for one-time preprocessing.

    Args:
        image_paths: List of image file paths
        target_size: Target resolution (default: 512)

    Returns:
        List of preprocessed PIL Images

    Raises:
        ValueError: When image file is corrupted or unsupported format
    """
    processed = []

    for path in image_paths:
        try:
            # Load and convert to RGB
            img = Image.open(path).convert("RGB")

            # Resize with high-quality resampling
            img = img.resize(
                (target_size, target_size),
                Image.Resampling.LANCZOS
            )

            processed.append(img)
            logger.debug(f"Preprocessed {path}: {img.size}, {img.mode}")

        except Exception as e:
            logger.error(f"Failed to preprocess {path}: {e}")
            raise ValueError(f"Invalid image file: {path}") from e

    logger.info(f"Successfully preprocessed {len(processed)} images")
    return processed


def validate_training_images(image_paths: List[str]) -> Tuple[List[str], List[str]]:
    """
    Validate training images and separate valid from invalid.

    Args:
        image_paths: List of image file paths to validate

    Returns:
        Tuple of (valid_paths, invalid_paths)
    """
    valid_paths = []
    invalid_paths = []

    for path in image_paths:
        try:
            if not os.path.exists(path):
                invalid_paths.append(path)
                continue

            with Image.open(path) as img:
                img.verify()

            with Image.open(path) as img:
                # Check size
                if img.width < 256 or img.height < 256:
                    logger.warning(f"Image too small: {path} ({img.size})")
                    invalid_paths.append(path)
                    continue

                # Check format
                if img.format not in ['JPEG', 'PNG', 'JPG']:
                    logger.warning(f"Unsupported format: {path} ({img.format})")
                    invalid_paths.append(path)
                    continue

                # Check file size (max 10MB as per TECHSPEC)
                file_size = os.path.getsize(path) / (1024 * 1024)  # MB
                if file_size > 10:
                    logger.warning(f"Image too large: {path} ({file_size:.2f}MB)")
                    invalid_paths.append(path)
                    continue

                valid_paths.append(path)

        except Exception as e:
            logger.error(f"Error validating {path}: {e}")
            invalid_paths.append(path)

    logger.info(f"Validation: {len(valid_paths)} valid, {len(invalid_paths)} invalid")
    return valid_paths, invalid_paths
