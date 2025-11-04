# Inference Server CODE_GUIDE

This document defines code writing patterns and rules for the **Inference Server**.

> **Note**: For common patterns (API response formats, error codes, etc.), refer to [docs/PATTERNS.md](../../docs/PATTERNS.md).

---

## Table of Contents

1. [Code Writing Principles](#1-code-writing-principles)
2. [Inference Pipeline Pattern](#2-inference-pipeline-pattern)
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
pillow>=10.0.0
boto3>=1.34.0
pika>=1.3.0
requests>=2.31.0
```

### 1.2 Project Structure

```
apps/inference-server/
├── generate.py           # Image generation pipeline
├── rabbitmq_consumer.py  # RabbitMQ message receiver
├── s3_uploader.py        # S3 generated image upload
├── webhook_client.py     # Backend Webhook caller
├── signature.py          # Artist signature watermark insertion
├── utils.py              # Common utilities
├── config.py             # Environment variable loader
├── requirements.txt
└── tests/
    ├── test_generate.py
    ├── test_signature.py
    └── test_webhook.py
```

### 1.3 Coding Style

- **Formatter**: Black (line-length=100)
- **Linter**: Pylint, Flake8
- **Type Hints**: Required for all functions
- **Docstring**: Google style

```python
def add_watermark(
    image: Image.Image,
    artist_name: str,
    position: str = "bottom-right",
    opacity: int = 128
) -> Image.Image:
    """
    Insert artist signature watermark.

    Args:
        image: Original PIL Image
        artist_name: Artist name
        position: Watermark position (bottom-right, bottom-left)
        opacity: Transparency (0-255)

    Returns:
        PIL Image with watermark inserted
    """
    watermark = create_text_overlay(artist_name, opacity)
    image.paste(watermark, get_position(image.size, position), watermark)
    return image
```

---

## 2. Inference Pipeline Pattern

### 2.1 LoRA-based Image Generation

**Core Principles**:
- Use Stable Diffusion 1.5 Base Model
- Dynamically load LoRA weights
- 50 Inference Steps (default)
- Send progress to Backend Webhook in real-time (0%, 25%, 50%, 75%, 90%)

```python
import torch
from diffusers import StableDiffusionPipeline, DPMSolverMultistepScheduler
from peft import PeftModel
import time

def generate_image(
    style_id: int,
    lora_model_path: str,
    prompt_tags: list[str],
    aspect_ratio: str = "1:1",
    seed: int = None,
    webhook_url: str = None,
    generation_id: int = None
) -> Image.Image:
    """Generate image based on LoRA."""

    # Load Base Model
    pipeline = StableDiffusionPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        torch_dtype=torch.float16
    )
    pipeline = pipeline.to("cuda")

    # Optimize Scheduler
    pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
        pipeline.scheduler.config
    )

    # Load LoRA weights
    pipeline.load_lora_weights(lora_model_path)

    # Calculate resolution
    width, height = get_resolution(aspect_ratio)

    # Generate Prompt
    prompt = " ".join(prompt_tags)

    # Generator (Seed reproducibility)
    generator = torch.Generator(device="cuda").manual_seed(seed or 42)

    # Send progress via Callback
    def progress_callback(step: int, timestep: int, latents: torch.Tensor):
        progress_percent = int((step / 50) * 100)
        milestones = [0, 25, 50, 75, 90]

        if progress_percent in milestones:
            send_progress(webhook_url, generation_id, step, 50)

    # Generate image
    image = pipeline(
        prompt=prompt,
        num_inference_steps=50,
        guidance_scale=7.5,
        width=width,
        height=height,
        generator=generator,
        callback=progress_callback,
        callback_steps=1
    ).images[0]

    return image


def get_resolution(aspect_ratio: str) -> tuple[int, int]:
    """Calculate resolution based on aspect ratio."""
    resolutions = {
        "1:1": (512, 512),
        "2:2": (768, 768),
        "1:2": (512, 1024)
    }
    return resolutions.get(aspect_ratio, (512, 512))
```

### 2.2 Scheduler Optimization

```python
from diffusers import DPMSolverMultistepScheduler, EulerDiscreteScheduler

# DPM-Solver++ (default, fast convergence)
pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
    pipeline.scheduler.config
)

# Or Euler Discrete (higher quality, slower)
pipeline.scheduler = EulerDiscreteScheduler.from_config(
    pipeline.scheduler.config
)
```

---

## 3. RabbitMQ Integration Pattern

### 3.1 Receive and Process Messages

```python
import pika
import json
from typing import Callable

def start_rabbitmq_consumer(
    queue_name: str = "image_generation",
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
def handle_generation_task(message: dict) -> None:
    """Process image generation task."""

    generation_id = message["generation_id"]
    style_id = message["style_id"]
    lora_model_url = message["lora_model_url"]
    prompt_tags = message["prompt_tags"]
    artist_name = message["artist_name"]
    seed = message.get("seed", 42)
    webhook_base_url = message["webhook_url"]

    try:
        # 1. Download LoRA model from S3
        lora_path = download_lora_model(lora_model_url)

        # 2. Generate image
        image = generate_image(
            style_id=style_id,
            lora_model_path=lora_path,
            prompt_tags=prompt_tags,
            seed=seed,
            webhook_url=f"{webhook_base_url}/api/webhooks/inference/progress",
            generation_id=generation_id
        )

        # 3. Insert artist signature watermark
        image_with_signature = add_watermark(image, artist_name)

        # 4. Upload to S3
        result_url = upload_image_to_s3(image_with_signature, generation_id)

        # 5. Send completion Webhook
        send_complete_webhook(
            url=f"{webhook_base_url}/api/webhooks/inference/complete",
            generation_id=generation_id,
            result_url=result_url,
            seed=seed
        )

    except Exception as e:
        # 6. Send failure Webhook
        send_failed_webhook(
            url=f"{webhook_base_url}/api/webhooks/inference/failed",
            generation_id=generation_id,
            error=str(e)
        )
```

---

## 4. S3 Storage Pattern

### 4.1 Download LoRA Model

```python
import boto3
from pathlib import Path

def download_lora_model(s3_url: str) -> str:
    """Download LoRA model from S3."""

    s3_client = boto3.client(
        "s3",
        aws_access_key_id=os.getenv("AWS_ACCESS_KEY_ID"),
        aws_secret_access_key=os.getenv("AWS_SECRET_ACCESS_KEY")
    )

    # s3://bucket/models/style_10/lora_weights.safetensors
    bucket, key = parse_s3_url(s3_url)
    local_path = f"/tmp/{Path(key).name}"

    s3_client.download_file(bucket, key, local_path)
    return local_path
```

### 4.2 Upload Generated Image

```python
def upload_image_to_s3(image: Image.Image, generation_id: int) -> str:
    """Upload generated image to S3 Public Bucket."""

    s3_client = boto3.client("s3")
    bucket = os.getenv("S3_BUCKET", "stylelicense-images")
    key = f"generations/gen_{generation_id}.jpg"

    # Save to temporary file then upload
    temp_path = f"/tmp/gen_{generation_id}.jpg"
    image.save(temp_path, format="JPEG", quality=95)

    s3_client.upload_file(
        temp_path,
        bucket,
        key,
        ExtraArgs={"ContentType": "image/jpeg", "ACL": "public-read"}
    )

    return f"https://{bucket}.s3.amazonaws.com/{key}"
```

---

## 5. Webhook Pattern

### 5.1 Send Progress

```python
import requests

def send_progress(
    webhook_url: str,
    generation_id: int,
    current_step: int,
    total_steps: int
) -> None:
    """Send progress to Backend in real-time."""

    progress_percent = int((current_step / total_steps) * 100)
    estimated_seconds = int((total_steps - current_step) * 0.1)  # Assume 0.1s/step

    payload = {
        "generation_id": generation_id,
        "progress": {
            "current_step": current_step,
            "total_steps": total_steps,
            "progress_percent": progress_percent,
            "estimated_seconds": estimated_seconds
        }
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('INTERNAL_API_TOKEN')}",
        "X-Request-Source": "inference-server",
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
def send_complete_webhook(
    url: str,
    generation_id: int,
    result_url: str,
    seed: int
) -> None:
    """Send generation completion Webhook."""

    payload = {
        "generation_id": generation_id,
        "result_url": result_url,
        "metadata": {
            "seed": seed,
            "steps": 50,
            "guidance_scale": 7.5
        }
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('INTERNAL_API_TOKEN')}",
        "X-Request-Source": "inference-server",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()


def send_failed_webhook(url: str, generation_id: int, error: str) -> None:
    """Send generation failure Webhook."""

    payload = {
        "generation_id": generation_id,
        "error_message": error,
        "error_code": "GENERATION_FAILED",
        "retry_count": 0
    }

    headers = {
        "Authorization": f"Bearer {os.getenv('INTERNAL_API_TOKEN')}",
        "X-Request-Source": "inference-server",
        "Content-Type": "application/json"
    }

    response = requests.post(url, json=payload, headers=headers, timeout=10)
    response.raise_for_status()
```

---

## 6. GPU Optimization

### 6.1 Memory-Efficient Pipeline Loading

```python
from diffusers import StableDiffusionPipeline

# Save memory with FP16
pipeline = StableDiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    variant="fp16"
)
pipeline = pipeline.to("cuda")

# CPU Offloading (when VRAM is insufficient)
pipeline.enable_sequential_cpu_offload()
```

### 6.2 Batch Processing Optimization

```python
# Generate multiple images simultaneously (if VRAM allows)
images = pipeline(
    prompt=[prompt] * 4,  # Generate 4 images at once
    num_inference_steps=50,
    guidance_scale=7.5
).images
```

### 6.3 Cache Cleanup

```python
import torch
import gc

# Clean up memory after generation
del pipeline
gc.collect()
torch.cuda.empty_cache()
```

---

## 7. Writing Tests

### 7.1 Artist Signature Watermark Test

```python
import pytest
from PIL import Image
from signature import add_watermark

def test_add_watermark():
    """Test watermark insertion."""
    image = Image.new("RGB", (512, 512), color="white")

    watermarked = add_watermark(image, artist_name="TestArtist", opacity=128)

    assert watermarked.size == (512, 512)
    assert watermarked.mode == "RGB"
    # Check if image was modified by watermark addition
    assert watermarked != image
```

### 7.2 Integration Test Example

```python
def test_webhook_complete(mocker):
    """Test completion Webhook sending."""
    mock_post = mocker.patch("requests.post")

    send_complete_webhook(
        url="http://localhost:8000/api/webhooks/inference/complete",
        generation_id=500,
        result_url="https://s3.../gen_500.jpg",
        seed=42
    )

    assert mock_post.called
    assert mock_post.call_args[1]["json"]["generation_id"] == 500
    assert mock_post.call_args[1]["json"]["metadata"]["seed"] == 42
```

---

## Reference Documents

- [TECHSPEC.md](../../TECHSPEC.md) - Overall system specification
- [docs/API.md](../../docs/API.md) - Backend API specification
- [docs/PATTERNS.md](../../docs/PATTERNS.md) - Common code patterns
- [PyTorch Docs](https://pytorch.org/docs/stable/)
- [Diffusers Docs](https://huggingface.co/docs/diffusers/)
- [PEFT Docs](https://huggingface.co/docs/peft/)
