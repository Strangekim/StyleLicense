"""
Tests for configuration module
"""

import pytest
from config import Config


def test_config_loading():
    """Test configuration loading"""
    assert Config.RABBITMQ_HOST is not None
    assert Config.BACKEND_URL is not None
    assert Config.TRAINING_QUEUE == "model_training"


def test_rabbitmq_url():
    """Test RabbitMQ URL generation"""
    url = Config.get_rabbitmq_url()
    assert "amqp://" in url
    assert Config.RABBITMQ_HOST in url


def test_webhook_headers():
    """Test webhook headers generation"""
    headers = Config.get_webhook_headers()
    assert "Authorization" in headers
    assert "X-Request-Source" in headers
    assert headers["X-Request-Source"] == "training-server"
    assert "Content-Type" in headers
