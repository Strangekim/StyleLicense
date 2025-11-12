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
    """
    Mock training task message

    Format matches PATTERNS.md specification:
    - task_id: UUID for task tracking
    - type: "model_training"
    - data: Contains style_id, images, tags, parameters
    """
    return {
        "task_id": "550e8400-e29b-41d4-a716-446655440000",
        "type": "model_training",
        "data": {
            "style_id": 123,
            "images": [
                "gs://stylelicense-media/training/image1.jpg",
                "gs://stylelicense-media/training/image2.jpg",
                "gs://stylelicense-media/training/image3.jpg",
            ],
            "tags": ["watercolor", "portrait", "vintage"],
            "parameters": {
                "epochs": 200,
                "learning_rate": 0.0001,
                "batch_size": 4,
            },
        },
        "callback_url": "https://api.stylelicense.com/api/webhooks/training/complete",
        "created_at": "2025-01-20T10:00:00.000Z",
    }
