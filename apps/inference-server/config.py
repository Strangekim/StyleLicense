"""
Configuration management for Inference Server.

Loads environment variables and validates required settings.
"""
import os
from dotenv import load_dotenv

load_dotenv()


class Config:
    """Configuration class for Inference Server."""

    # RabbitMQ Configuration
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

    # Queue names
    QUEUE_IMAGE_GENERATION = "image_generation"

    # Backend API Configuration
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "test-integration-token")

    # Google Cloud Storage Configuration
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "stylelicense-media")
    GCS_PROJECT_ID = os.getenv("GCS_PROJECT_ID", "stylelicense")

    # Inference Configuration (for M4 phase)
    MODEL_STORAGE_PATH = os.getenv("MODEL_STORAGE_PATH", "./models")
    MAX_CONCURRENT_GENERATIONS = int(os.getenv("MAX_CONCURRENT_GENERATIONS", "10"))

    # Generation Settings
    INFERENCE_STEPS = int(os.getenv("INFERENCE_STEPS", "50"))
    GUIDANCE_SCALE = float(os.getenv("GUIDANCE_SCALE", "7.5"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "inference_server.log")

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    @classmethod
    def validate(cls):
        """Validate required configuration fields."""
        required_fields = [
            ("RABBITMQ_HOST", cls.RABBITMQ_HOST),
            ("BACKEND_URL", cls.BACKEND_URL),
        ]

        missing_fields = [
            field_name for field_name, field_value in required_fields if not field_value
        ]

        if missing_fields:
            raise ValueError(
                f"Missing required configuration fields: {', '.join(missing_fields)}"
            )

    @classmethod
    def get_rabbitmq_url(cls):
        """Get RabbitMQ connection URL."""
        return (
            f"amqp://{cls.RABBITMQ_USER}:{cls.RABBITMQ_PASSWORD}@"
            f"{cls.RABBITMQ_HOST}:{cls.RABBITMQ_PORT}{cls.RABBITMQ_VHOST}"
        )

    @classmethod
    def get_webhook_headers(cls):
        """Get headers for webhook requests to backend."""
        return {
            "Authorization": f"Bearer {cls.INTERNAL_API_TOKEN}",
            "X-Request-Source": "inference-server",
            "Content-Type": "application/json",
        }
