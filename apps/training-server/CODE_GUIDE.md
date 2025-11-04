# Training Server CODE_GUIDE

This document defines code writing patterns and rules for the **Training Server**.

> **Note**: For common patterns (API response formats, error codes, etc.), refer to [docs/PATTERNS.md](../../docs/PATTERNS.md).

---

## Table of Contents

1. [Code Writing Principles](#1-code-writing-principles)
2. [Training Pipeline Pattern](#2-training-pipeline-pattern)
3. [RabbitMQ Integration Pattern](#3-rabbitmq-integration-pattern)
4. [S3 Storage Pattern](#4-s3-storage-pattern)
5. [Webhook Pattern](#5-webhook-pattern)
6. [GPU Optimization](#6-gpu-optimization)
7. [Writing Tests](#7-writing-tests)

---

## 1. Code Writing Principles

### 1.1 Version Compatibility

**Library versions based on TECHSPEC.md**:
```python
# requirements.txt
torch>=2.0.0
diffusers>=0.30.0
peft>=0.13.0
transformers>=4.40.0
accelerate>=0.30.0
pillow>=10.0.0
boto3>=1.34.0
pika>=1.3.0
requests>=2.31.0
```

### 1.2 Project Structure

```
apps/training-server/
├── train.py              # Training pipeline entry point
├── rabbitmq_consumer.py  # RabbitMQ message receiver
├── s3_uploader.py        # S3 training image/model upload
├── webhook_client.py     # Backend Webhook caller
├── utils.py              # Common utilities
├── config.py             # Environment variable loader
├── requirements.txt
└── tests/
    ├── test_train.py
    ├── test_rabbitmq.py
    └── test_webhook.py
```

### 1.3 Coding Style

- **Formatter**: Black (line-length=100)
- **Linter**: Pylint, Flake8
- **Type Hints**: Required for all functions
- **Docstring**: Google style

```python
def preprocess_images(image_paths: list[str], target_size: int = 512) -> list[Image.Image]:
    """
    Preprocess training images (resize, normalize).

    Args:
        image_paths: List of image file paths
        target_size: Target resolution (default: 512)

    Returns:
        List of preprocessed PIL Images

    Raises:
        ValueError: When image file is corrupted or unsupported format
    """
    processed = []
    for path in image_paths:
        img = Image.open(path).convert("RGB")
        img = img.resize((target_size, target_size), Image.LANCZOS)
        processed.append(img)
    return processed
```

---

## 2. Training Pipeline Pattern

### 2.1 LoRA Training Pipeline

**Core Principles**:
- Stable Diffusion 1.5 based Fine-tuning
- PEFT LoRA usage (Rank 16, Alpha 32)
- Mixed Precision Training (FP16)
- Send progress to Backend Webhook every 30 seconds

```python
import torch
from diffusers import StableDiffusionPipeline, DDPMScheduler
from peft import LoraConfig, get_peft_model
from accelerate import Accelerator
import time
import requests

def train_lora_model(
    style_id: int,
    train_image_paths: list[str],
    output_dir: str,
    num_epochs: int = 100,
    learning_rate: float = 1e-4,
    webhook_url: str = None
) -> str:
    """Execute LoRA Fine-tuning."""

    # Initialize Accelerator (Mixed Precision)
    accelerator = Accelerator(mixed_precision="fp16")

    # Load Base Model
    pipeline = StableDiffusionPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        torch_dtype=torch.float16
    )
    unet = pipeline.unet

    # LoRA Config
    lora_config = LoraConfig(
        r=16,  # Rank
        lora_alpha=32,
        target_modules=["to_q", "to_k", "to_v", "to_out.0"],
        lora_dropout=0.1,
        bias="none"
    )

    # Apply LoRA to UNet
    unet = get_peft_model(unet, lora_config)
    unet.train()

    # Optimizer
    optimizer = torch.optim.AdamW(unet.parameters(), lr=learning_rate)

    # Wrap with Accelerate
    unet, optimizer = accelerator.prepare(unet, optimizer)

    # Training Loop
    last_webhook_time = time.time()

    for epoch in range(num_epochs):
        for step, batch in enumerate(train_dataloader):
            with accelerator.accumulate(unet):
                latents = vae.encode(batch["images"]).latent_dist.sample()
                noise = torch.randn_like(latents)
                timesteps = torch.randint(0, 1000, (latents.shape[0],))

                noisy_latents = noise_scheduler.add_noise(latents, noise, timesteps)
                pred_noise = unet(noisy_latents, timesteps, batch["prompts"]).sample

                loss = torch.nn.functional.mse_loss(pred_noise, noise)
                accelerator.backward(loss)
                optimizer.step()
                optimizer.zero_grad()

        # Send progress every 30 seconds
        current_time = time.time()
        if current_time - last_webhook_time >= 30:
            send_progress(webhook_url, style_id, epoch, num_epochs)
            last_webhook_time = current_time

    # Save LoRA weights
    unet.save_pretrained(output_dir)
    return output_dir
```

### 2.2 Memory Optimization

**Enable Gradient Checkpointing**:
```python
from diffusers import StableDiffusionPipeline

pipeline = StableDiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16
)

# Enable Gradient Checkpointing
pipeline.unet.enable_gradient_checkpointing()
```

**Prevent Memory Leaks**:
```python
# ❌ Bad: Accumulates autograd history
total_loss = 0
for epoch in range(100):
    loss = compute_loss()
    total_loss += loss  # Computation graph retained

# ✅ Good: Convert to float
total_loss = 0
for epoch in range(100):
    loss = compute_loss()
    total_loss += float(loss)  # Computation graph released
```

---

## 3. RabbitMQ Integration Pattern

### 3.1 Receive and Process Messages

```python
import pika
import json
from typing import Callable

def start_rabbitmq_consumer(
    queue_name: str = "model_training",
    callback: Callable[[dict], None] = None
) -> None:
    """Start RabbitMQ Consumer."""

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST", "localhost"))
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    def on_message(ch, method, properties, body):
        try:
            message = json.loads(body)
            print(f"[RabbitMQ] Received: {message}")

            # Process message
            callback(message)

            # ACK
            ch.basic_ack(delivery_tag=method.delivery_tag)

        except Exception as e:
            print(f"[RabbitMQ] Error: {e}")
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=False)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue=queue_name, on_message_callback=on_message)

    print(f"[RabbitMQ] Waiting for messages in '{queue_name}'...")
    channel.start_consuming()
```

### 3.2 Message Processing Handler

```python
def handle_training_task(message: dict) -> None:
    """Process training task."""

    style_id = message["style_id"]
    image_urls = message["image_urls"]
    webhook_base_url = message["webhook_url"]

    try:
        # 1. Download training images from S3
        image_paths = download_training_images(image_urls)

        # 2. Execute LoRA training
        model_path = train_lora_model(
            style_id=style_id,
            train_image_paths=image_paths,
            output_dir=f"/tmp/lora_{style_id}",
            webhook_url=f"{webhook_base_url}/api/webhooks/training/progress"
        )

        # 3. Upload trained model to S3
        model_url = upload_model_to_s3(model_path, style_id)

        # 4. Send completion Webhook
        send_complete_webhook(
            url=f"{webhook_base_url}/api/webhooks/training/complete",
            style_id=style_id,
            model_url=model_url
        )

    except Exception as e:
        # 5. Send failure Webhook
        send_failed_webhook(
            url=f"{webhook_base_url}/api/webhooks/training/failed",
            style_id=style_id,
            error=str(e)
        )
```

---

## 4. S3 Storage Pattern

### 4.1 Download Training Images

```python
import boto3
from pathlib import Path

def download_training_images(s3_urls: list[str]) -> list[str]:
    """Download training images from S3."""

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

    local_paths = []

    for url in s3_urls:
        # s3://bucket/path/to/image.jpg → bucket, path/to/image.jpg
        bucket, key = parse_s3_url(url)
        local_path = f"/tmp/{Path(key).name}"

        s3_client.download_file(bucket, key, local_path)
        local_paths.append(local_path)

    return local_paths
```

### 4.2 Upload Model

```python
def upload_model_to_s3(model_dir: str, style_id: int) -> str:
    """Upload trained LoRA model to S3."""

    s3_client = boto3.client("s3")
    bucket = os.getenv("S3_BUCKET", "stylelicense-models")
    key = f"models/style_{style_id}/lora_weights.safetensors"

    # Upload model file
    model_file = f"{model_dir}/adapter_model.safetensors"
    s3_client.upload_file(model_file, bucket, key)

    return f"s3://{bucket}/{key}"
```

---

## 5. Webhook Pattern

### 5.1 Send Progress

```python
import requests

def send_progress(
    webhook_url: str,
    style_id: int,
    current_epoch: int,
    total_epochs: int
) -> None:
    """Send progress to Backend every 30 seconds."""

    progress_percent = int((current_epoch / total_epochs) * 100)
    estimated_seconds = int((total_epochs - current_epoch) * 36)  # Assume 36s/epoch

    payload = {
        "style_id": style_id,
        "progress": {
            "current_epoch": current_epoch,
            "total_epochs": total_epochs,
            "progress_percent": progress_percent,
            "estimated_seconds": estimated_seconds
        }
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('INTERNAL_API_TOKEN')}",
        "X-Request-Source": "training-server",
        "Content-Type": "application/json"
    }

    try:
        response = requests.patch(webhook_url, json=payload, headers=headers, timeout=10)
        response.raise_for_status()
    except requests.RequestException as e:
        print(f"[Webhook] Failed to send progress: {e}")
```

### 5.2 Complete/Failure Webhooks

```python
def send_complete_webhook(url: str, style_id: int, model_url: str) -> None:
    """Send training completion Webhook."""

    payload = {
        "style_id": style_id,
        "model_url": model_url,
        "metadata": {
            "training_epochs": 100,
            "lora_rank": 16,
            "lora_alpha": 32
        }
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('INTERNAL_API_TOKEN')}",
        "X-Request-Source": "training-server",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()


def send_failed_webhook(url: str, style_id: int, error: str) -> None:
    """Send training failure Webhook."""

    payload = {
        "style_id": style_id,
        "error_message": error,
        "error_code": "TRAINING_FAILED"
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('INTERNAL_API_TOKEN')}",
        "X-Request-Source": "training-server",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
```

---

## 6. GPU Optimization

### 6.1 Mixed Precision Training

```python
from accelerate import Accelerator

# Initialize Accelerator
accelerator = Accelerator(mixed_precision="fp16")

# Wrap model, Optimizer
model, optimizer = accelerator.prepare(model, optimizer)

# Forward/Backward
with accelerator.accumulate(model):
    loss = compute_loss()
    accelerator.backward(loss)
    optimizer.step()
    optimizer.zero_grad()
```

### 6.2 GPU Memory Management

```python
import torch

# Explicitly delete unused tensors
del intermediate_tensor
torch.cuda.empty_cache()

# Disable gradients with Context Manager
with torch.no_grad():
    val_loss = model(val_batch)
```

### 6.3 VRAM Monitoring

```python
def log_gpu_memory():
    """Log GPU memory usage."""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3  # GB
        reserved = torch.cuda.memory_reserved() / 1024**3
        print(f"[GPU] Allocated: {allocated:.2f}GB, Reserved: {reserved:.2f}GB")
```

---

## 7. Writing Tests

### 7.1 Unit Test Example

```python
import pytest
from train import preprocess_images

def test_preprocess_images():
    """Test image preprocessing."""
    image_paths = ["test_data/img1.jpg", "test_data/img2.png"]

    processed = preprocess_images(image_paths, target_size=512)

    assert len(processed) == 2
    assert processed[0].size == (512, 512)
    assert processed[1].mode == "RGB"
```

### 7.2 Integration Test Example

```python
def test_webhook_progress(mocker):
    """Test progress Webhook sending."""
    mock_post = mocker.patch("requests.patch")

    send_progress(
        webhook_url="http://localhost:8000/api/webhooks/training/progress",
        style_id=10,
        current_epoch=50,
        total_epochs=100
    )

    assert mock_post.called
    assert mock_post.call_args[1]["json"]["style_id"] == 10
    assert mock_post.call_args[1]["json"]["progress"]["progress_percent"] == 50
```

---

## Reference Documents

- [TECHSPEC.md](../../TECHSPEC.md) - Overall system specification
- [docs/API.md](../../docs/API.md) - Backend API specification
- [docs/PATTERNS.md](../../docs/PATTERNS.md) - Common code patterns
- [PyTorch Docs](https://pytorch.org/docs/stable/)
- [Diffusers Docs](https://huggingface.co/docs/diffusers/)
- [PEFT Docs](https://huggingface.co/docs/peft/)
