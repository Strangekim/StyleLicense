# Inference Server Dockerfile for Image Generation
# Requires NVIDIA GPU with CUDA support

FROM nvidia/cuda:12.1.0-cudnn8-runtime-ubuntu22.04

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PIP_NO_CACHE_DIR=1 \
    DEBIAN_FRONTEND=noninteractive

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3.11 \
    python3-pip \
    git \
    wget \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip
RUN python3 -m pip install --upgrade pip

# Copy requirements first (for better caching)
COPY requirements.txt .

# Install PyTorch with CUDA support
RUN pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# Install other Python dependencies
RUN pip install -r requirements.txt

# Copy project files
COPY . .

# Create directories for temporary files and generated images
RUN mkdir -p /tmp/models /tmp/generations

# Create a non-root user (optional, but recommended)
RUN useradd -m -u 1000 inference && \
    chown -R inference:inference /app /tmp/models /tmp/generations

USER inference

# Health check (checks if the consumer is running)
HEALTHCHECK --interval=60s --timeout=10s --start-period=30s --retries=3 \
    CMD python3 -c "import pika; conn = pika.BlockingConnection(pika.ConnectionParameters(host='${RABBITMQ_HOST:-rabbitmq}'))" || exit 1

# Default command: Start RabbitMQ consumer
CMD ["python3", "rabbitmq_consumer.py"]
