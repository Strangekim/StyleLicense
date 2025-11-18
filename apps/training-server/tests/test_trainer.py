"""Tests for training/trainer.py"""

import pytest
import tempfile
import os
from pathlib import Path
from PIL import Image
from training.trainer import LoRATrainer


@pytest.fixture
def temp_images():
    """Create temporary test images."""
    with tempfile.TemporaryDirectory() as tmpdir:
        temp_files = []
        for i in range(5):
            img = Image.new('RGB', (512, 512), color=(i * 50, i * 50, i * 50))
            path = os.path.join(tmpdir, f"test_{i}.jpg")
            img.save(path, 'JPEG')
            temp_files.append(path)
        yield temp_files


@pytest.fixture
def output_dir():
    """Create temporary output directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


def test_lora_trainer_initialization(output_dir):
    """Test LoRATrainer initialization."""
    trainer = LoRATrainer(
        style_id=1,
        output_dir=output_dir,
        num_epochs=10,
        learning_rate=1e-4
    )

    assert trainer.style_id == 1
    assert trainer.num_epochs == 10
    assert trainer.learning_rate == 1e-4
    assert trainer.lora_rank == 8
    assert trainer.lora_alpha == 32
    assert trainer.output_dir == Path(output_dir)


def test_lora_trainer_output_dir_creation(output_dir):
    """Test that output directory is created."""
    nested_dir = os.path.join(output_dir, "nested", "path")

    trainer = LoRATrainer(
        style_id=1,
        output_dir=nested_dir
    )

    assert os.path.exists(nested_dir)


def test_create_dataloader(output_dir, temp_images):
    """Test dataloader creation."""
    trainer = LoRATrainer(
        style_id=1,
        output_dir=output_dir,
        batch_size=2
    )

    dataloader = trainer._create_dataloader(temp_images)

    assert dataloader is not None
    assert len(dataloader.dataset) == 5
    assert dataloader.batch_size == 2


def test_trainer_parameters():
    """Test trainer with custom parameters."""
    with tempfile.TemporaryDirectory() as tmpdir:
        trainer = LoRATrainer(
            style_id=999,
            output_dir=tmpdir,
            lora_rank=16,
            lora_alpha=64,
            learning_rate=5e-5,
            num_epochs=200,
            batch_size=4
        )

        assert trainer.lora_rank == 16
        assert trainer.lora_alpha == 64
        assert trainer.learning_rate == 5e-5
        assert trainer.num_epochs == 200
        assert trainer.batch_size == 4


# Note: Full training tests are skipped as they require:
# 1. Downloading large SD models (multiple GB)
# 2. Significant GPU memory (8-16GB)
# 3. Long execution time (minutes to hours)
#
# These should be tested manually in GPU environment or through integration tests
