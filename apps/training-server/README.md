# Training Server

## Overview

LoRA (Low-Rank Adaptation) 기반의 Stable Diffusion 파인튜닝 서버입니다. RabbitMQ에서 학습 태스크를 수신하여 사용자가 업로드한 이미지로 스타일 모델을 학습하고, 학습 진행률과 결과를 Backend API로 전송합니다.

**핵심 역할:**
- RabbitMQ Consumer (`model_training` 큐)
- LoRA 파인튜닝 실행 (Stable Diffusion v1.5)
- 학습 진행률 주기적 리포팅
- 체크포인트 관리 및 S3 업로드
- 학습 완료/실패 webhook 전송

---

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Language | Python | 3.11+ | Core language |
| ML Framework | PyTorch | 2.1+ | Deep learning |
| Diffusion | Diffusers (Hugging Face) | 0.25+ | Stable Diffusion models |
| LoRA | PEFT | 0.8+ | Parameter-Efficient Fine-Tuning |
| Message Queue | RabbitMQ (pika) | 1.3+ | Task queue consumer |
| Storage | AWS S3 (boto3) | 1.34+ | Model weights storage |
| HTTP Client | requests | 2.31+ | Webhook callbacks |
| GPU | CUDA | 11.8+ | GPU acceleration |
| Testing | pytest | 8.0+ | Unit tests |
| Code Quality | black, pylint | 23.12+, 3.0+ | Formatting, linting |

---

## Directory Structure

```
apps/training-server/
├── main.py                     # Entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
│
├── consumer/                   # RabbitMQ consumer
│   ├── __init__.py
│   └── training_consumer.py   # Queue consumer logic
│
├── training/                   # LoRA training logic
│   ├── __init__.py
│   ├── trainer.py             # Main training loop
│   ├── lora_config.py         # LoRA hyperparameters
│   ├── dataset.py             # Custom dataset loader
│   └── checkpoint.py          # Checkpoint management
│
├── services/                   # External service clients
│   ├── __init__.py
│   ├── s3_service.py          # S3 upload/download
│   └── webhook_service.py     # Backend API callbacks
│
├── utils/                      # Utility functions
│   ├── __init__.py
│   ├── logger.py              # Logging setup
│   └── gpu_monitor.py         # GPU utilization tracking
│
├── tests/                      # Test suite
│   ├── conftest.py            # pytest fixtures
│   ├── test_trainer.py
│   ├── test_dataset.py
│   └── test_integration.py
│
├── Dockerfile                  # Container image
├── .env.example               # Environment variables template
├── pytest.ini                 # pytest configuration
├── .pylintrc                  # pylint configuration
├── PLAN.md                    # Development task plan
├── CODE_GUIDE.md              # Code patterns & conventions
└── README.md                  # This file
```

---

## Architecture

### LoRA Training Pipeline

사용자 이미지로 Stable Diffusion 모델을 파인튜닝하는 파이프라인입니다.

```
RabbitMQ Queue
  ↓
Training Consumer (메시지 수신)
  ↓
S3 Service (학습 이미지 다운로드)
  ↓
LoRA Trainer (모델 학습)
  ├─ Dataset 준비
  ├─ LoRA Config 적용
  ├─ Training Loop 실행
  ├─ Checkpoint 저장 (10 epoch마다)
  └─ 진행률 리포팅 (30초마다)
  ↓
S3 Service (모델 weights 업로드)
  ↓
Webhook Service (학습 완료 통보)
```

**주요 컴포넌트:**
- `TrainingConsumer`: RabbitMQ에서 학습 태스크 수신
- `LoRATrainer`: Stable Diffusion v1.5 + LoRA 학습
- `S3Service`: 이미지/모델 다운로드/업로드
- `WebhookService`: Backend API로 진행률/결과 전송

### Data Flow

#### 모델 학습 플로우
```
Backend → RabbitMQ: 학습 태스크 발행
RabbitMQ → Training Server: 태스크 수신
Training Server → S3: 이미지 다운로드 (10-30장)
Training Server: LoRA Fine-tuning (100-500 epochs)
Training Server → Backend: 진행률 리포팅 (30초마다, PATCH /api/webhooks/training/progress)
Training Server → S3: 체크포인트 저장 (10 epoch마다)
Training Server → S3: 최종 모델 업로드 (.safetensors)
Training Server → Backend: POST /api/webhooks/training/complete
Backend → Frontend: 학습 완료 알림
```

**상세 API 명세**: [docs/API.md#10-webhook-api](../../docs/API.md#10-webhook-api)

**학습 파라미터 (TECHSPEC.md 및 PLAN.md 기반):**
- Base Model: Stable Diffusion v1.5
- LoRA Rank: 8
- Learning Rate: 1e-4
- Epochs: 100-500 (이미지 수에 따라)
- Batch Size: 1
- GPU Memory: 8GB+ VRAM 권장

---

## Development Setup

### Prerequisites
- Python 3.11+
- CUDA 11.8+ (NVIDIA GPU required)
- GPU Memory: 최소 8GB VRAM (RTX 3060 이상 권장)
- RabbitMQ 3.12+
- AWS S3: 버킷 및 IAM 권한

### Installation

```bash
# 1. Virtual environment 생성
cd apps/training-server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Dependencies 설치
pip install -r requirements.txt

# 3. CUDA 확인
python -c "import torch; print(torch.cuda.is_available())"
# True 출력되어야 함

# 4. 환경변수 설정
cp .env.example .env
# .env 파일 수정

# 5. 실행
python main.py
```

### Environment Variables

```bash
# RabbitMQ
RABBITMQ_HOST=...
RABBITMQ_PORT=5672
RABBITMQ_USER=user
RABBITMQ_PASS=password

# AWS S3 (IAM User Access Key)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_STORAGE_BUCKET_NAME=stylelicense-media
AWS_S3_REGION_NAME=ap-northeast-2

# Backend API (운영 서버의 도메인 - HTTPS 사용)
BACKEND_API_URL=https://stylelicense.com
INTERNAL_API_TOKEN=your_internal_token  # 32자 이상 랜덤 UUID

# GPU
CUDA_VISIBLE_DEVICES=0

# Logging
LOG_LEVEL=INFO
```

---

## Development Workflow

### Running Tests

```bash
# 전체 테스트 실행
pytest

# Coverage 리포트
pytest --cov=training --cov-report=html

# GPU 필요한 테스트 스킵 (CPU 환경)
pytest -m "not gpu"
```

### Code Quality

```bash
# Format
black .

# Lint
pylint training/ services/ consumer/
```

---

## Testing Strategy

### Test Types

| Type | Coverage | Tools |
|------|----------|-------|
| Unit Tests | 60% | pytest |
| Integration Tests | 30% | pytest + S3/RabbitMQ mocks |
| GPU Tests | 10% | pytest (requires GPU) |

**Test Fixtures**: `tests/conftest.py`
**Coverage Goal**: 70%

---

## Deployment

### Production Checklist

**GPU 서버: RunPod RTX 4090 24GB**

- [ ] **RunPod GPU Pod 생성**
  - GPU: RTX 4090 (24GB VRAM)
  - Template: Custom Docker Image
  - Image: `<registry>/stylelicense-training:latest`
- [ ] CUDA 11.8+ 포함된 Docker 이미지 사용
- [ ] **RabbitMQ 연결 설정**
  - `RABBITMQ_HOST=<Backend-EC2-Public-IP>`
  - Backend EC2의 RabbitMQ 포트(5672)를 Public으로 노출 또는 VPN 사용
  - 방화벽: RunPod Pod IP를 Backend EC2 Security Group에 허용
- [ ] **S3 버킷 설정**
  - 학습 이미지: Private Bucket (`stylelicense-training-data`)
  - 모델 파일: Private Bucket (`stylelicense-models`)
  - **AWS Access Key 환경변수** 설정 (RunPod Pod에서 S3 접근)
- [ ] **Backend API 연결 설정**
  - `BACKEND_API_URL=https://stylelicense.com` (도메인 사용)
  - `INTERNAL_API_TOKEN=<32자-UUID>` (Webhook 인증용)
  - Backend EC2 Security Group: 443 포트 허용 (RunPod IP 또는 전체)
- [ ] GPU 메모리 프로파일링 (24GB 이내 사용)
- [ ] 로깅 설정 (RunPod 콘솔 또는 CloudWatch)
- [ ] Checkpoint 저장 경로 설정
- [ ] 로그 수집 (CloudWatch, Sentry)

### Running in Production

```bash
# Docker 실행 (GPU 사용)
docker run --gpus all \
    -e RABBITMQ_HOST=rabbitmq \
    -e AWS_ACCESS_KEY_ID=$AWS_KEY \
    -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET \
    -e INTERNAL_API_TOKEN=$TOKEN \
    training-server
```

---

## Monitoring

### Metrics to Monitor

- 학습 진행률 (epoch, loss)
- GPU 메모리 사용량
- GPU 활용률 (utilization)
- RabbitMQ 큐 길이
- 학습 성공/실패 비율
- 평균 학습 시간 (per style)

---

## References

### 필수 문서
- **[CODE_GUIDE.md](CODE_GUIDE.md)** - 코드 작성 패턴 및 예제 (코드 작성 전 필독)
- **[PLAN.md](PLAN.md)** - 개발 작업 계획 (다음 작업 확인)

### 프로젝트 문서
- **[TECHSPEC.md](../../TECHSPEC.md)** - 전체 시스템 아키텍처
- **[docs/PATTERNS.md](../../docs/PATTERNS.md)** - 메시지 포맷 (RabbitMQ)

### 외부 문서
- **Diffusers**: https://huggingface.co/docs/diffusers
- **PEFT (LoRA)**: https://huggingface.co/docs/peft
- **PyTorch**: https://pytorch.org/docs/stable/

---

## Troubleshooting

### Common Issues

**1. CUDA not available**
```bash
# CUDA 설치 확인
nvidia-smi

# PyTorch CUDA 버전 확인
python -c "import torch; print(torch.version.cuda)"
```

**2. RabbitMQ connection refused**
```bash
docker ps | grep rabbitmq
docker restart rabbitmq
```

**3. Out of memory**
```bash
# Batch size 줄이기 (config.py)
# Gradient checkpointing 활성화
# Mixed precision training 사용 (FP16)
```

---

## Support

- **GitHub Issues**: 버그 리포트 및 기능 제안
- **Team Communication**: Slack #ai-training 채널
- **Documentation**: [TECHSPEC.md](../../TECHSPEC.md)
