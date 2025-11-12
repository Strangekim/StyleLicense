"""
Configuration module for Training Server

Loads and validates environment variables for the training server.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for Training Server"""

    # RabbitMQ Configuration
    RABBITMQ_HOST = os.getenv("RABBITMQ_HOST", "localhost")
    RABBITMQ_PORT = int(os.getenv("RABBITMQ_PORT", "5672"))
    RABBITMQ_USER = os.getenv("RABBITMQ_USER", "guest")
    RABBITMQ_PASSWORD = os.getenv("RABBITMQ_PASSWORD", "guest")
    RABBITMQ_VHOST = os.getenv("RABBITMQ_VHOST", "/")

    # Queue names
    TRAINING_QUEUE = "model_training"

    # Backend API Configuration
    BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8000")
    INTERNAL_API_TOKEN = os.getenv("INTERNAL_API_TOKEN", "")

    # Google Cloud Storage Configuration
    GCS_BUCKET_NAME = os.getenv("GCS_BUCKET_NAME", "stylelicense-media")
    GCS_PROJECT_ID = os.getenv("GCS_PROJECT_ID", "stylelicense")
    GOOGLE_APPLICATION_CREDENTIALS = os.getenv("GOOGLE_APPLICATION_CREDENTIALS", "")

    # Training Configuration
    MODEL_STORAGE_PATH = os.getenv("MODEL_STORAGE_PATH", "./models")
    CHECKPOINT_INTERVAL = int(os.getenv("CHECKPOINT_INTERVAL", "10"))
    MAX_RETRY_ATTEMPTS = int(os.getenv("MAX_RETRY_ATTEMPTS", "3"))

    # Logging
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE = os.getenv("LOG_FILE", "training_server.log")

    # Environment
    ENVIRONMENT = os.getenv("ENVIRONMENT", "development")

    @classmethod
    def validate(cls):
        """Validate required configuration"""
        errors = []

        # Check required fields
        if not cls.RABBITMQ_HOST:
            errors.append("RABBITMQ_HOST is required")

        if not cls.BACKEND_URL:
            errors.append("BACKEND_URL is required")

        if cls.ENVIRONMENT == "production":
            if not cls.INTERNAL_API_TOKEN:
                errors.append("INTERNAL_API_TOKEN is required in production")

            if not cls.GOOGLE_APPLICATION_CREDENTIALS:
                errors.append("GOOGLE_APPLICATION_CREDENTIALS is required in production")

        if errors:
            raise ValueError(f"Configuration errors: {', '.join(errors)}")

        return True

    @classmethod
    def get_rabbitmq_url(cls):
        """Get RabbitMQ connection URL"""
        return (
            f"amqp://{cls.RABBITMQ_USER}:{cls.RABBITMQ_PASSWORD}"
            f"@{cls.RABBITMQ_HOST}:{cls.RABBITMQ_PORT}{cls.RABBITMQ_VHOST}"
        )

    @classmethod
    def get_webhook_headers(cls):
        """Get headers for webhook requests to backend"""
        return {
            "Authorization": f"Bearer {cls.INTERNAL_API_TOKEN}",
            "X-Request-Source": "training-server",
            "Content-Type": "application/json",
        }


# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    if Config.ENVIRONMENT == "production":
        raise
    print(f"Configuration warning: {e}")
