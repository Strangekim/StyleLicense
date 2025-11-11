"""
Training Server Main Entry Point

Starts the RabbitMQ consumer for processing training tasks.
"""

import sys
import torch
from config import Config
from utils.logger import logger
from consumer.training_consumer import TrainingConsumer


def check_cuda():
    """Check CUDA availability and log GPU information"""
    logger.info("Checking CUDA availability...")

    if torch.cuda.is_available():
        gpu_count = torch.cuda.device_count()
        logger.info(f"CUDA is available! Found {gpu_count} GPU(s)")

        for i in range(gpu_count):
            gpu_name = torch.cuda.get_device_name(i)
            gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
            logger.info(f"GPU {i}: {gpu_name} ({gpu_memory:.2f} GB)")

        # Test simple tensor operation on GPU
        try:
            x = torch.tensor([1.0, 2.0, 3.0]).cuda()
            y = x * 2
            logger.info(f"GPU tensor test successful: {y.cpu().tolist()}")
        except Exception as e:
            logger.error(f"GPU tensor test failed: {e}")
    else:
        logger.warning("CUDA is not available. Training will run on CPU (not recommended for production)")

    return torch.cuda.is_available()


def main():
    """Main entry point"""
    logger.info("="*50)
    logger.info("Starting Training Server")
    logger.info("="*50)

    # Log configuration
    logger.info(f"Environment: {Config.ENVIRONMENT}")
    logger.info(f"RabbitMQ Host: {Config.RABBITMQ_HOST}")
    logger.info(f"Backend URL: {Config.BACKEND_URL}")
    logger.info(f"GCS Bucket: {Config.GCS_BUCKET_NAME}")

    # Check CUDA (optional for M1, required for M4)
    cuda_available = check_cuda()

    if Config.ENVIRONMENT == "production" and not cuda_available:
        logger.error("CUDA is required in production environment")
        sys.exit(1)

    # Create and start consumer
    consumer = TrainingConsumer()

    try:
        logger.info("Starting consumer...")
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
        consumer.stop_consuming()
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)

    logger.info("Training Server stopped")


if __name__ == "__main__":
    main()
