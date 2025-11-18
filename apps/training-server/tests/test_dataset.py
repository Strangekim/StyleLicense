"""Tests for training/dataset.py"""

import pytest
import torch
from PIL import Image
import os
import tempfile
from training.dataset import (
    StyleImageDataset,
    preprocess_images,
    validate_training_images
)


@pytest.fixture
def temp_images():
    """Create temporary test images."""
    temp_files = []

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create valid test images
        for i in range(3):
            img = Image.new('RGB', (512, 512), color=(i * 50, i * 50, i * 50))
            path = os.path.join(tmpdir, f"test_{i}.jpg")
            img.save(path, 'JPEG')
            temp_files.append(path)

        yield temp_files


def test_style_image_dataset_initialization(temp_images):
    """Test StyleImageDataset initialization."""
    dataset = StyleImageDataset(temp_images, target_size=512)

    assert len(dataset) == 3
    assert dataset.target_size == 512
    assert dataset.normalize is True


def test_style_image_dataset_getitem(temp_images):
    """Test dataset __getitem__ method."""
    dataset = StyleImageDataset(temp_images, target_size=512)

    image_tensor, path = dataset[0]

    assert isinstance(image_tensor, torch.Tensor)
    assert image_tensor.shape == (3, 512, 512)
    assert path in temp_images


def test_style_image_dataset_empty_paths():
    """Test dataset with empty paths."""
    with pytest.raises(ValueError, match="image_paths cannot be empty"):
        StyleImageDataset([])


def test_preprocess_images(temp_images):
    """Test preprocess_images function."""
    processed = preprocess_images(temp_images, target_size=512)

    assert len(processed) == 3
    assert all(isinstance(img, Image.Image) for img in processed)
    assert all(img.size == (512, 512) for img in processed)
    assert all(img.mode == "RGB" for img in processed)


def test_preprocess_images_invalid_path():
    """Test preprocess_images with invalid path."""
    with pytest.raises(ValueError, match="Invalid image file"):
        preprocess_images(["/nonexistent/path.jpg"])


def test_validate_training_images(temp_images):
    """Test validate_training_images function."""
    valid, invalid = validate_training_images(temp_images)

    assert len(valid) == 3
    assert len(invalid) == 0
    assert all(path in temp_images for path in valid)


def test_validate_training_images_with_invalid():
    """Test validation with mix of valid and invalid paths."""
    valid_paths = []

    with tempfile.TemporaryDirectory() as tmpdir:
        # Create one valid image
        img = Image.new('RGB', (512, 512), color=(100, 100, 100))
        valid_path = os.path.join(tmpdir, "valid.jpg")
        img.save(valid_path, 'JPEG')
        valid_paths.append(valid_path)

        # Add invalid paths
        paths = [valid_path, "/nonexistent.jpg", "/another/invalid.png"]

        valid, invalid = validate_training_images(paths)

        assert len(valid) == 1
        assert len(invalid) == 2
        assert valid[0] == valid_path


def test_style_image_dataset_small_image():
    """Test dataset skips images that are too small."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create image that's too small (< 256x256)
        img = Image.new('RGB', (128, 128), color=(100, 100, 100))
        small_path = os.path.join(tmpdir, "small.jpg")
        img.save(small_path, 'JPEG')

        # Create valid image
        img2 = Image.new('RGB', (512, 512), color=(100, 100, 100))
        valid_path = os.path.join(tmpdir, "valid.jpg")
        img2.save(valid_path, 'JPEG')

        dataset = StyleImageDataset([small_path, valid_path])

        # Should only include the valid image
        assert len(dataset) == 1


def test_preprocess_images_different_sizes():
    """Test preprocessing images of different sizes."""
    with tempfile.TemporaryDirectory() as tmpdir:
        sizes = [(1024, 768), (800, 600), (512, 512)]
        paths = []

        for i, size in enumerate(sizes):
            img = Image.new('RGB', size, color=(100, 100, 100))
            path = os.path.join(tmpdir, f"img_{i}.jpg")
            img.save(path, 'JPEG')
            paths.append(path)

        processed = preprocess_images(paths, target_size=512)

        assert len(processed) == 3
        assert all(img.size == (512, 512) for img in processed)
