"""
Inference Server Entry Point

Starts the RabbitMQ consumer to process image generation tasks.
"""
import logging
import sys
from config import Config
from consumer.generation_consumer import GenerationConsumer

# Setup logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL.upper()),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler(Config.LOG_FILE) if Config.LOG_FILE else logging.NullHandler(),
    ],
)

logger = logging.getLogger("inference-server")


def check_dependencies():
    """
    Check if required dependencies are available.

    For M1 phase, we don't require GPU/torch.
    For M4 phase, this will check for CUDA availability.
    """
    logger.info("Checking dependencies...")

    # Try to import torch (optional for M1, required for M4)
    try:
        import torch
        if torch.cuda.is_available():
            gpu_count = torch.cuda.device_count()
            logger.info(f"CUDA is available! Found {gpu_count} GPU(s)")

            for i in range(gpu_count):
                gpu_name = torch.cuda.get_device_name(i)
                gpu_memory = torch.cuda.get_device_properties(i).total_memory / (1024**3)
                logger.info(f"GPU {i}: {gpu_name} ({gpu_memory:.2f} GB)")

            # Test simple tensor operation on GPU
            x = torch.tensor([1.0, 2.0, 3.0]).cuda()
            y = x * 2
            logger.info(f"GPU test successful: {y.cpu().tolist()}")
        else:
            logger.warning("CUDA is not available. Inference will run on CPU (not recommended for production)")

    except ImportError:
        logger.warning("PyTorch not installed. This is OK for M1 phase (mock generation only)")
        logger.warning("For M4 phase (actual inference), install torch with: pip install torch")

    # Check GCS credentials (optional for M1)
    try:
        from google.cloud import storage
        # Try to create a client (will fail if credentials are not set)
        client = storage.Client()
        logger.info(f"GCS client initialized successfully")
    except Exception as e:
        logger.warning(f"GCS credentials not found. GCS functionality will be disabled.")
        logger.warning(f"Error: {e}")


def main():
    """Main entry point."""
    logger.info("=" * 50)
    logger.info("Starting Inference Server")
    logger.info("=" * 50)

    # Log configuration
    logger.info(f"Environment: {Config.ENVIRONMENT}")
    logger.info(f"RabbitMQ Host: {Config.RABBITMQ_HOST}")
    logger.info(f"Backend URL: {Config.BACKEND_URL}")
    logger.info(f"GCS Bucket: {Config.GCS_BUCKET_NAME}")
    logger.info(f"Max Concurrent Generations: {Config.MAX_CONCURRENT_GENERATIONS}")
    logger.info(f"Inference Steps: {Config.INFERENCE_STEPS}")

    # Validate configuration
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Configuration validation failed: {e}")
        sys.exit(1)

    # Check dependencies
    check_dependencies()

    # Create and start consumer
    logger.info("Starting consumer...")
    consumer = GenerationConsumer()

    try:
        consumer.connect()
        consumer.start_consuming()
    except KeyboardInterrupt:
        logger.info("Received interrupt signal, shutting down...")
        consumer.stop()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
