# Inference Server CODE_GUIDE

이 문서는 **Inference Server**의 코드 작성 패턴과 규칙을 정의합니다.

> **참고**: 공통 패턴(API 응답 형식, 에러 코드 등)은 [docs/PATTERNS.md](../../docs/PATTERNS.md)를 참조하세요.

---

## 목차

1. [코드 작성 원칙](#1-코드-작성-원칙)
2. [Inference Pipeline 패턴](#2-inference-pipeline-패턴)
3. [RabbitMQ Integration 패턴](#3-rabbitmq-integration-패턴)
4. [S3 Storage 패턴](#4-s3-storage-패턴)
5. [Webhook 패턴](#5-webhook-패턴)
6. [GPU 최적화](#6-gpu-최적화)
7. [테스트 작성](#7-테스트-작성)

---

## 1. 코드 작성 원칙

### 1.1 버전 호환성

**TECHSPEC.md 기준 라이브러리 버전**:
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

### 1.2 프로젝트 구조

```
apps/inference-server/
├── generate.py           # Image generation pipeline
├── rabbitmq_consumer.py  # RabbitMQ 메시지 수신
├── s3_uploader.py        # S3 생성 이미지 업로드
├── webhook_client.py     # Backend Webhook 호출
├── signature.py          # 작가 서명(시그니처) 워터마크 삽입
├── utils.py              # 공통 유틸리티
├── config.py             # 환경 변수 로드
├── requirements.txt
└── tests/
    ├── test_generate.py
    ├── test_signature.py
    └── test_webhook.py
```

### 1.3 코딩 스타일

- **포맷터**: Black (line-length=100)
- **린터**: Pylint, Flake8
- **타입 힌트**: 모든 함수에 타입 힌트 필수
- **Docstring**: Google 스타일

```python
def add_watermark(
    image: Image.Image,
    artist_name: str,
    position: str = "bottom-right",
    opacity: int = 128
) -> Image.Image:
    """
    작가 서명(시그니처) 워터마크 삽입.

    Args:
        image: 원본 PIL Image
        artist_name: 작가 이름
        position: 워터마크 위치 (bottom-right, bottom-left)
        opacity: 투명도 (0-255)

    Returns:
        워터마크가 삽입된 PIL Image
    """
    watermark = create_text_overlay(artist_name, opacity)
    image.paste(watermark, get_position(image.size, position), watermark)
    return image
```

---

## 2. Inference Pipeline 패턴

### 2.1 LoRA 기반 이미지 생성

**핵심 원칙**:
- Stable Diffusion 1.5 Base Model 사용
- LoRA 가중치 동적 로드
- 50 Inference Steps (기본값)
- 진행률 실시간 Backend Webhook 전송 (0%, 25%, 50%, 75%, 90%)

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
    """LoRA 기반 이미지 생성."""

    # Base Model 로드
    pipeline = StableDiffusionPipeline.from_pretrained(
        "stable-diffusion-v1-5/stable-diffusion-v1-5",
        torch_dtype=torch.float16
    )
    pipeline = pipeline.to("cuda")

    # Scheduler 최적화
    pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
        pipeline.scheduler.config
    )

    # LoRA 가중치 로드
    pipeline.load_lora_weights(lora_model_path)

    # 해상도 계산
    width, height = get_resolution(aspect_ratio)

    # Prompt 생성
    prompt = " ".join(prompt_tags)

    # Generator (Seed 재현성)
    generator = torch.Generator(device="cuda").manual_seed(seed or 42)

    # Callback으로 진행률 전송
    def progress_callback(step: int, timestep: int, latents: torch.Tensor):
        progress_percent = int((step / 50) * 100)
        milestones = [0, 25, 50, 75, 90]

        if progress_percent in milestones:
            send_progress(webhook_url, generation_id, step, 50)

    # 이미지 생성
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
    """Aspect ratio에 따른 해상도 계산."""
    resolutions = {
        "1:1": (512, 512),
        "2:2": (768, 768),
        "1:2": (512, 1024)
    }
    return resolutions.get(aspect_ratio, (512, 512))
```

### 2.2 Scheduler 최적화

```python
from diffusers import DPMSolverMultistepScheduler, EulerDiscreteScheduler

# DPM-Solver++ (기본값, 빠른 수렴)
pipeline.scheduler = DPMSolverMultistepScheduler.from_config(
    pipeline.scheduler.config
)

# 또는 Euler Discrete (더 높은 품질, 느림)
pipeline.scheduler = EulerDiscreteScheduler.from_config(
    pipeline.scheduler.config
)
```

---

## 3. RabbitMQ Integration 패턴

### 3.1 메시지 수신 및 처리

```python
import pika
import json
from typing import Callable

def start_rabbitmq_consumer(
    queue_name: str = "image_generation",
    callback: Callable[[dict], None] = None
) -> None:
    """RabbitMQ Consumer 시작."""

    connection = pika.BlockingConnection(
        pika.ConnectionParameters(host=os.getenv("RABBITMQ_HOST", "localhost"))
    )
    channel = connection.channel()
    channel.queue_declare(queue=queue_name, durable=True)

    def on_message(ch, method, properties, body):
        try:
            message = json.loads(body)
            print(f"[RabbitMQ] Received: {message}")

            # 메시지 처리
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

### 3.2 메시지 처리 핸들러

```python
def handle_generation_task(message: dict) -> None:
    """이미지 생성 작업 처리."""

    generation_id = message["generation_id"]
    style_id = message["style_id"]
    lora_model_url = message["lora_model_url"]
    prompt_tags = message["prompt_tags"]
    artist_name = message["artist_name"]
    seed = message.get("seed", 42)
    webhook_base_url = message["webhook_url"]

    try:
        # 1. S3에서 LoRA 모델 다운로드
        lora_path = download_lora_model(lora_model_url)

        # 2. 이미지 생성
        image = generate_image(
            style_id=style_id,
            lora_model_path=lora_path,
            prompt_tags=prompt_tags,
            seed=seed,
            webhook_url=f"{webhook_base_url}/api/webhooks/inference/progress",
            generation_id=generation_id
        )

        # 3. 작가 서명(시그니처) 워터마크 삽입
        image_with_signature = add_watermark(image, artist_name)

        # 4. S3 업로드
        result_url = upload_image_to_s3(image_with_signature, generation_id)

        # 5. 완료 Webhook 전송
        send_complete_webhook(
            url=f"{webhook_base_url}/api/webhooks/inference/complete",
            generation_id=generation_id,
            result_url=result_url,
            seed=seed
        )

    except Exception as e:
        # 6. 실패 Webhook 전송
        send_failed_webhook(
            url=f"{webhook_base_url}/api/webhooks/inference/failed",
            generation_id=generation_id,
            error=str(e)
        )
```

---

## 4. S3 Storage 패턴

### 4.1 LoRA 모델 다운로드

```python
import boto3
from pathlib import Path

def download_lora_model(s3_url: str) -> str:
    """S3에서 LoRA 모델 다운로드."""

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

### 4.2 생성 이미지 업로드

```python
def upload_image_to_s3(image: Image.Image, generation_id: int) -> str:
    """생성 이미지 S3 Public Bucket 업로드."""

    s3_client = boto3.client("s3")
    bucket = os.getenv("S3_BUCKET", "stylelicense-images")
    key = f"generations/gen_{generation_id}.jpg"

    # 임시 파일로 저장 후 업로드
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

## 5. Webhook 패턴

### 5.1 진행률 전송

```python
import requests

def send_progress(
    webhook_url: str,
    generation_id: int,
    current_step: int,
    total_steps: int
) -> None:
    """실시간 Backend로 진행률 전송."""

    progress_percent = int((current_step / total_steps) * 100)
    estimated_seconds = int((total_steps - current_step) * 0.1)  # 0.1초/step 가정

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

### 5.2 완료/실패 Webhook

```python
def send_complete_webhook(
    url: str,
    generation_id: int,
    result_url: str,
    seed: int
) -> None:
    """생성 완료 Webhook 전송."""

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
    """생성 실패 Webhook 전송."""

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

## 6. GPU 최적화

### 6.1 메모리 효율적인 Pipeline 로드

```python
from diffusers import StableDiffusionPipeline

# FP16으로 메모리 절약
pipeline = StableDiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16,
    variant="fp16"
)
pipeline = pipeline.to("cuda")

# CPU Offloading (VRAM 부족 시)
pipeline.enable_sequential_cpu_offload()
```

### 6.2 배치 처리 최적화

```python
# 여러 이미지 동시 생성 (VRAM 허용 시)
images = pipeline(
    prompt=[prompt] * 4,  # 4장 동시 생성
    num_inference_steps=50,
    guidance_scale=7.5
).images
```

### 6.3 캐시 정리

```python
import torch
import gc

# 생성 완료 후 메모리 정리
del pipeline
gc.collect()
torch.cuda.empty_cache()
```

---

## 7. 테스트 작성

### 7.1 작가 서명(시그니처) 워터마크 테스트

```python
import pytest
from PIL import Image
from signature import add_watermark

def test_add_watermark():
    """워터마크 삽입 테스트."""
    image = Image.new("RGB", (512, 512), color="white")

    watermarked = add_watermark(image, artist_name="TestArtist", opacity=128)

    assert watermarked.size == (512, 512)
    assert watermarked.mode == "RGB"
    # 워터마크가 추가되어 이미지가 변경되었는지 확인
    assert watermarked != image
```

### 7.2 Integration Test 예시

```python
def test_webhook_complete(mocker):
    """완료 Webhook 전송 테스트."""
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

## 참고 문서

- [TECHSPEC.md](../../TECHSPEC.md) - 전체 시스템 명세
- [docs/API.md](../../docs/API.md) - Backend API 명세
- [docs/PATTERNS.md](../../docs/PATTERNS.md) - 공통 코드 패턴
- [PyTorch Docs](https://pytorch.org/docs/stable/)
- [Diffusers Docs](https://huggingface.co/docs/diffusers/)
- [PEFT Docs](https://huggingface.co/docs/peft/)
