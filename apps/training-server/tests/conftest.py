"""
Pytest configuration and fixtures
"""

import os
import pytest


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables"""
    os.environ["ENVIRONMENT"] = "test"
    os.environ["RABBITMQ_HOST"] = "localhost"
    os.environ["BACKEND_URL"] = "http://localhost:8000"
    os.environ["INTERNAL_API_TOKEN"] = "test-token"
    os.environ["GCS_BUCKET_NAME"] = "test-bucket"
    os.environ["LOG_LEVEL"] = "DEBUG"


@pytest.fixture
def mock_training_message():
    """Mock training task message"""
    return {
        "task_id": "test-task-123",
        "type": "model_training",
        "data": {
            "style_id": 1,
            "image_paths": [
                "gs://test-bucket/training/img1.jpg",
                "gs://test-bucket/training/img2.jpg",
            ],
            "num_epochs": 100,
        },
    }
