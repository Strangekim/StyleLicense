# Training Server CODE_GUIDE

이 문서는 **Training Server**의 코드 작성 패턴과 규칙을 정의합니다.

> **참고**: 공통 패턴(API 응답 형식, 에러 코드 등)은 [docs/PATTERNS.md](../../docs/PATTERNS.md)를 참조하세요.

---

## 목차

1. [코드 작성 원칙](#1-코드-작성-원칙)
2. [Training Pipeline 패턴](#2-training-pipeline-패턴)
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
accelerate>=0.30.0
pillow>=10.0.0
boto3>=1.34.0
pika>=1.3.0
requests>=2.31.0
```

### 1.2 프로젝트 구조

```
apps/training-server/
├── train.py              # Training pipeline 진입점
├── rabbitmq_consumer.py  # RabbitMQ 메시지 수신
├── s3_uploader.py        # S3 학습 이미지/모델 업로드
├── webhook_client.py     # Backend Webhook 호출
├── utils.py              # 공통 유틸리티
├── config.py             # 환경 변수 로드
├── requirements.txt
└── tests/
    ├── test_train.py
    ├── test_rabbitmq.py
    └── test_webhook.py
```

### 1.3 코딩 스타일

- **포맷터**: Black (line-length=100)
- **린터**: Pylint, Flake8
- **타입 힌트**: 모든 함수에 타입 힌트 필수
- **Docstring**: Google 스타일

```python
def preprocess_images(image_paths: list[str], target_size: int = 512) -> list[Image.Image]:
    """
    학습 이미지 전처리 (리사이즈, 정규화).

    Args:
        image_paths: 이미지 파일 경로 리스트
        target_size: 타겟 해상도 (기본값: 512)

    Returns:
        전처리된 PIL Image 리스트

    Raises:
        ValueError: 이미지 파일이 손상되었거나 지원하지 않는 포맷일 때
    """
    processed = []
    for path in image_paths:
        img = Image.open(path).convert("RGB")
        img = img.resize((target_size, target_size), Image.LANCZOS)
        processed.append(img)
    return processed
```

---

## 2. Training Pipeline 패턴

### 2.1 LoRA 학습 파이프라인

**핵심 원칙**:
- Stable Diffusion 1.5 기반 Fine-tuning
- PEFT LoRA 사용 (Rank 16, Alpha 32)
- Mixed Precision Training (FP16)
- 진행률 30초마다 Backend Webhook 전송

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
    """LoRA Fine-tuning 실행."""

    # Accelerator 초기화 (Mixed Precision)
    accelerator = Accelerator(mixed_precision="fp16")

    # Base Model 로드
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

    # UNet에 LoRA 적용
    unet = get_peft_model(unet, lora_config)
    unet.train()

    # Optimizer
    optimizer = torch.optim.AdamW(unet.parameters(), lr=learning_rate)

    # Accelerate로 감싸기
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

        # 30초마다 진행률 전송
        current_time = time.time()
        if current_time - last_webhook_time >= 30:
            send_progress(webhook_url, style_id, epoch, num_epochs)
            last_webhook_time = current_time

    # LoRA 가중치 저장
    unet.save_pretrained(output_dir)
    return output_dir
```

### 2.2 메모리 최적화

**Gradient Checkpointing 활성화**:
```python
from diffusers import StableDiffusionPipeline

pipeline = StableDiffusionPipeline.from_pretrained(
    "stable-diffusion-v1-5/stable-diffusion-v1-5",
    torch_dtype=torch.float16
)

# Gradient Checkpointing 활성화
pipeline.unet.enable_gradient_checkpointing()
```

**메모리 누수 방지**:
```python
# ❌ 나쁜 예: Autograd history 축적
total_loss = 0
for epoch in range(100):
    loss = compute_loss()
    total_loss += loss  # 계산 그래프 유지됨

# ✅ 좋은 예: float으로 변환
total_loss = 0
for epoch in range(100):
    loss = compute_loss()
    total_loss += float(loss)  # 계산 그래프 해제
```

---

## 3. RabbitMQ Integration 패턴

### 3.1 메시지 수신 및 처리

```python
import pika
import json
from typing import Callable

def start_rabbitmq_consumer(
    queue_name: str = "model_training",
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
def handle_training_task(message: dict) -> None:
    """학습 작업 처리."""

    style_id = message["style_id"]
    image_urls = message["image_urls"]
    webhook_base_url = message["webhook_url"]

    try:
        # 1. S3에서 학습 이미지 다운로드
        image_paths = download_training_images(image_urls)

        # 2. LoRA 학습 실행
        model_path = train_lora_model(
            style_id=style_id,
            train_image_paths=image_paths,
            output_dir=f"/tmp/lora_{style_id}",
            webhook_url=f"{webhook_base_url}/api/webhooks/training/progress"
        )

        # 3. 학습된 모델 S3 업로드
        model_url = upload_model_to_s3(model_path, style_id)

        # 4. 완료 Webhook 전송
        send_complete_webhook(
            url=f"{webhook_base_url}/api/webhooks/training/complete",
            style_id=style_id,
            model_url=model_url
        )

    except Exception as e:
        # 5. 실패 Webhook 전송
        send_failed_webhook(
            url=f"{webhook_base_url}/api/webhooks/training/failed",
            style_id=style_id,
            error=str(e)
        )
```

---

## 4. S3 Storage 패턴

### 4.1 학습 이미지 다운로드

```python
import boto3
from pathlib import Path

def download_training_images(s3_urls: list[str]) -> list[str]:
    """S3에서 학습 이미지 다운로드."""

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

### 4.2 모델 업로드

```python
def upload_model_to_s3(model_dir: str, style_id: int) -> str:
    """학습된 LoRA 모델 S3 업로드."""

    s3_client = boto3.client("s3")
    bucket = os.getenv("S3_BUCKET", "stylelicense-models")
    key = f"models/style_{style_id}/lora_weights.safetensors"

    # 모델 파일 업로드
    model_file = f"{model_dir}/adapter_model.safetensors"
    s3_client.upload_file(model_file, bucket, key)

    return f"s3://{bucket}/{key}"
```

---

## 5. Webhook 패턴

### 5.1 진행률 전송

```python
import requests

def send_progress(
    webhook_url: str,
    style_id: int,
    current_epoch: int,
    total_epochs: int
) -> None:
    """30초마다 Backend로 진행률 전송."""

    progress_percent = int((current_epoch / total_epochs) * 100)
    estimated_seconds = int((total_epochs - current_epoch) * 36)  # 36초/epoch 가정

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

### 5.2 완료/실패 Webhook

```python
def send_complete_webhook(url: str, style_id: int, model_url: str) -> None:
    """학습 완료 Webhook 전송."""

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
    """학습 실패 Webhook 전송."""

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

## 6. GPU 최적화

### 6.1 Mixed Precision Training

```python
from accelerate import Accelerator

# Accelerator 초기화
accelerator = Accelerator(mixed_precision="fp16")

# 모델, Optimizer 감싸기
model, optimizer = accelerator.prepare(model, optimizer)

# Forward/Backward
with accelerator.accumulate(model):
    loss = compute_loss()
    accelerator.backward(loss)
    optimizer.step()
    optimizer.zero_grad()
```

### 6.2 GPU 메모리 관리

```python
import torch

# 사용하지 않는 텐서 명시적 삭제
del intermediate_tensor
torch.cuda.empty_cache()

# Context Manager로 그래디언트 비활성화
with torch.no_grad():
    val_loss = model(val_batch)
```

### 6.3 VRAM 모니터링

```python
def log_gpu_memory():
    """GPU 메모리 사용량 로깅."""
    if torch.cuda.is_available():
        allocated = torch.cuda.memory_allocated() / 1024**3  # GB
        reserved = torch.cuda.memory_reserved() / 1024**3
        print(f"[GPU] Allocated: {allocated:.2f}GB, Reserved: {reserved:.2f}GB")
```

---

## 7. 테스트 작성

### 7.1 Unit Test 예시

```python
import pytest
from train import preprocess_images

def test_preprocess_images():
    """이미지 전처리 테스트."""
    image_paths = ["test_data/img1.jpg", "test_data/img2.png"]

    processed = preprocess_images(image_paths, target_size=512)

    assert len(processed) == 2
    assert processed[0].size == (512, 512)
    assert processed[1].mode == "RGB"
```

### 7.2 Integration Test 예시

```python
def test_webhook_progress(mocker):
    """진행률 Webhook 전송 테스트."""
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

## 참고 문서

- [TECHSPEC.md](../../TECHSPEC.md) - 전체 시스템 명세
- [docs/API.md](../../docs/API.md) - Backend API 명세
- [docs/PATTERNS.md](../../docs/PATTERNS.md) - 공통 코드 패턴
- [PyTorch Docs](https://pytorch.org/docs/stable/)
- [Diffusers Docs](https://huggingface.co/docs/diffusers/)
- [PEFT Docs](https://huggingface.co/docs/peft/)
