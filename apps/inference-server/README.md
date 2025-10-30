# Inference Server

## Overview

Stable Diffusion 기반의 이미지 생성 서버입니다. RabbitMQ에서 생성 요청을 수신하여 사용자가 학습한 LoRA 스타일 모델을 적용한 이미지를 생성하고, 워터마크를 삽입하여 S3에 업로드합니다.

**핵심 역할:**
- RabbitMQ Consumer (`image_generation` 큐)
- Stable Diffusion 이미지 생성 (LoRA weights 적용)
- 워터마크(시그니처) 삽입
- 배치 처리 (최대 10개 동시 생성)
- 생성 진행률 리포팅
- 완료/실패 webhook 전송

---

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Language | Python | 3.11+ | Core language |
| ML Framework | PyTorch | 2.1+ | Deep learning |
| Diffusion | Diffusers (Hugging Face) | 0.25+ | Stable Diffusion inference |
| Image Processing | Pillow (PIL) | 10.1+ | Watermark insertion |
| Message Queue | RabbitMQ (pika) | 1.3+ | Task queue consumer |
| Storage | AWS S3 (boto3) | 1.34+ | Image storage |
| HTTP Client | requests | 2.31+ | Webhook callbacks |
| GPU | CUDA | 11.8+ | GPU acceleration |
| Testing | pytest | 8.0+ | Unit tests |
| Code Quality | black, pylint | 23.12+, 3.0+ | Formatting, linting |

---

## Directory Structure

```
apps/inference-server/
├── main.py                     # Entry point
├── config.py                   # Configuration management
├── requirements.txt            # Python dependencies
│
├── consumer/                   # RabbitMQ consumer
│   ├── __init__.py
│   └── generation_consumer.py # Queue consumer logic
│
├── inference/                  # Image generation logic
│   ├── __init__.py
│   ├── generator.py           # Main generation pipeline
│   ├── lora_loader.py         # LoRA weight loading
│   └── scheduler_config.py    # Diffusion scheduler settings
│
├── watermark/                  # Signature insertion
│   ├── __init__.py
│   └── inserter.py            # Watermark insertion logic
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
│   ├── test_generator.py
│   ├── test_watermark.py
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

### Image Generation Pipeline

사용자 프롬프트와 LoRA 스타일을 결합하여 이미지를 생성하는 파이프라인입니다.

```
RabbitMQ Queue
  ↓
Generation Consumer (메시지 수신)
  ↓
S3 Service (LoRA weights 다운로드)
  ↓
Image Generator (이미지 생성)
  ├─ Stable Diffusion Pipeline 로드
  ├─ LoRA Weights 적용
  ├─ 이미지 생성 (50 steps)
  └─ 진행률 리포팅
  ↓
Watermark Inserter (서명 삽입)
  ├─ 아티스트 이름 추가
  ├─ 위치/투명도 설정
  └─ 이미지 합성
  ↓
S3 Service (이미지 업로드)
  ↓
Webhook Service (생성 완료 통보)
```

**주요 컴포넌트:**
- `GenerationConsumer`: RabbitMQ에서 생성 태스크 수신 (최대 10개 동시)
- `ImageGenerator`: Stable Diffusion v1.5 + LoRA 추론
- `WatermarkInserter`: PIL 기반 시그니처 삽입
- `S3Service`: LoRA 모델/이미지 다운로드/업로드
- `WebhookService`: Backend API로 진행률/결과 전송

### Data Flow

#### 이미지 생성 플로우
```
Backend → RabbitMQ: 생성 태스크 발행
RabbitMQ → Inference Server: 태스크 수신
Inference Server → S3: LoRA weights 다운로드
Inference Server: Stable Diffusion 추론 (50 steps)
Inference Server → Backend: 진행률 리포팅 (0%, 25%, 50%, 75%, 90%)
Inference Server: 워터마크 삽입 (아티스트 서명)
Inference Server → S3: 생성된 이미지 업로드 (.png)
Inference Server → Backend: POST /api/webhooks/generation/complete
Backend → Frontend: 이미지 URL 반환
```

**생성 파라미터 (TECHSPEC.md 기반):**
- Base Model: Stable Diffusion v1.5
- Sampling Steps: 50
- Guidance Scale: 7.5
- Image Size: 512x512
- Scheduler: DPM-Solver++ (빠른 추론)
- Batch Size: 1-4 (동시 생성)

---

## Development Setup

### Prerequisites
- Python 3.11+
- CUDA 11.8+ (NVIDIA GPU required)
- GPU Memory: 최소 6GB VRAM (RTX 3060 이상 권장)
- RabbitMQ 3.12+
- AWS S3: 버킷 및 IAM 권한

### Installation

```bash
# 1. Virtual environment 생성
cd apps/inference-server
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

# Backend API (운영 서버의 Public IP 또는 도메인)
BACKEND_API_URL=http://<your-backend-server-ip>:8000
INTERNAL_API_TOKEN=your_internal_token

# GPU
CUDA_VISIBLE_DEVICES=0

# Batch Processing
MAX_CONCURRENT_GENERATIONS=10

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
pytest --cov=inference --cov-report=html

# GPU 필요한 테스트 스킵 (CPU 환경)
pytest -m "not gpu"
```

### Code Quality

```bash
# Format
black .

# Lint
pylint inference/ services/ consumer/ watermark/
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

- [ ] CUDA 11.8+ 설치
- [ ] NVIDIA Docker runtime 설정
- [ ] RabbitMQ 클러스터 연결
- [ ] S3 버킷 설정 및 접근을 위한 **AWS Access Key 환경변수** 확인
- [ ] `INTERNAL_API_TOKEN` 환경변수 설정
- [ ] GPU 메모리 프로파일링
- [ ] Font 파일 설치 (워터마크용)
- [ ] 로그 수집 (CloudWatch, Sentry)
- [ ] Model caching 전략 수립

### Running in Production

```bash
# Docker 실행 (GPU 사용)
docker run --gpus all \
    -e RABBITMQ_HOST=rabbitmq \
    -e AWS_ACCESS_KEY_ID=$AWS_KEY \
    -e AWS_SECRET_ACCESS_KEY=$AWS_SECRET \
    -e INTERNAL_API_TOKEN=$TOKEN \
    -e MAX_CONCURRENT_GENERATIONS=10 \
    inference-server
```

---

## Monitoring

### Metrics to Monitor

- 생성 시간 (per image)
- GPU 메모리 사용량
- GPU 활용률 (utilization)
- RabbitMQ 큐 길이
- 생성 성공/실패 비율
- 평균 생성 시간 (steps per second)

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
- **Stable Diffusion**: https://github.com/CompVis/stable-diffusion
- **PyTorch**: https://pytorch.org/docs/stable/
- **Pillow (PIL)**: https://pillow.readthedocs.io/

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

**2. Out of memory**
```bash
# Attention slicing 활성화 (config.py)
# Steps 줄이기 (30 steps)
# Batch size 1로 설정
```

**3. Font not found (워터마크)**
```bash
# Debian/Ubuntu
apt-get install fonts-dejavu-core

# Alpine
apk add ttf-dejavu
```

**4. Slow generation**
```bash
# xFormers 활성화
# DPM-Solver++ scheduler 사용 (기본값)
# Model caching 활성화
```

---

## Support

- **GitHub Issues**: 버그 리포트 및 기능 제안
- **Team Communication**: Slack #ai-inference 채널
- **Documentation**: [TECHSPEC.md](../../TECHSPEC.md)
