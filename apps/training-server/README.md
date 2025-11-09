# Training Server

## Overview

LoRA (Low-Rank Adaptation) based Stable Diffusion fine-tuning server. Receives training tasks from RabbitMQ, trains style models with user-uploaded images, and sends training progress and results to Backend API.

**Core Responsibilities:**
- RabbitMQ Consumer (`model_training` queue)
- Execute LoRA fine-tuning (Stable Diffusion v1.5)
- Periodic progress reporting
- Checkpoint management and S3 upload
- Send training complete/failed webhooks

---

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Language | Python | 3.11+ | Core language |
| ML Framework | PyTorch | 2.1+ | Deep learning |
| Diffusion | Diffusers (Hugging Face) | 0.25+ | Stable Diffusion models |
| LoRA | PEFT | 0.8+ | Parameter-Efficient Fine-Tuning |
| Message Queue | RabbitMQ (pika) | 1.3+ | Task queue consumer |
| Storage | Google Cloud Storage (google-cloud-storage) | 2.14+ | Model weights storage |
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
│   ├── gcs_service.py           # Cloud Storage upload/download
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

Pipeline for fine-tuning Stable Diffusion model with user images.

```
RabbitMQ Queue
  ↓
Training Consumer (receive message)
  ↓
Cloud Storage Service (download training images)
  ↓
LoRA Trainer (train model)
  ├─ Prepare dataset
  ├─ Apply LoRA config
  ├─ Execute training loop
  ├─ Save checkpoint (every 10 epochs)
  └─ Report progress (every 30 seconds)
  ↓
Cloud Storage Service (upload model weights)
  ↓
Webhook Service (notify training complete)
```

**Main Components:**
- `TrainingConsumer`: Receive training tasks from RabbitMQ
- `LoRATrainer`: Stable Diffusion v1.5 + LoRA training
- `GCSService`: Download/upload images/models from/to Google Cloud Storage
- `WebhookService`: Send progress/results to Backend API

### Data Flow

#### Model Training Flow
```
Backend → RabbitMQ: Publish training task
RabbitMQ → Training Server: Receive task
Training Server → Cloud Storage: Download images (10-30 images)
Training Server: LoRA Fine-tuning (100-500 epochs)
Training Server → Backend: Report progress (every 30 seconds, PATCH /api/webhooks/training/progress)
Training Server → Cloud Storage: Save checkpoints (every 10 epochs)
Training Server → Cloud Storage: Upload final model (.safetensors)
Training Server → Backend: POST /api/webhooks/training/complete
Backend → Frontend: Training complete notification
```

**Detailed API spec**: [docs/API.md#10-webhook-api](../../docs/API.md#10-webhook-api)

**Training parameters (based on TECHSPEC.md and PLAN.md):**
- Base Model: Stable Diffusion v1.5
- LoRA Rank: 8
- Learning Rate: 1e-4
- Epochs: 100-500 (depending on number of images)
- Batch Size: 1
- GPU Memory: 8GB+ VRAM recommended

---

## Development Setup

### Prerequisites
- Python 3.11+
- CUDA 11.8+ (NVIDIA GPU required)
- GPU Memory: Minimum 8GB VRAM (NVIDIA T4 or higher recommended)
- RabbitMQ 3.12+
- Google Cloud Storage: Bucket and IAM permissions

### Installation

```bash
# 1. Create virtual environment
cd apps/training-server
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements.txt

# 3. Verify CUDA
python -c "import torch; print(torch.cuda.is_available())"
# Should output True

# 4. Set environment variables
cp .env.example .env
# Edit .env file

# 5. Run
python main.py
```

### Environment Variables

```bash
# RabbitMQ
RABBITMQ_HOST=...
RABBITMQ_PORT=5672
RABBITMQ_USER=user
RABBITMQ_PASS=password

# Google Cloud Storage
# GCE VM에 연결된 서비스 계정을 통해 자동으로 인증되므로 별도 키 파일 불필요.
# 코드에서는 버킷 이름만 지정하면 됩니다.
GCS_BUCKET_NAME=stylelicense-media

# Backend API (production server domain - use HTTPS)
BACKEND_API_URL=https://api.stylelicense.com
INTERNAL_API_TOKEN=your_internal_token  # 32+ character random UUID

# GPU
CUDA_VISIBLE_DEVICES=0

# Logging
LOG_LEVEL=INFO
```

---

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Coverage report
pytest --cov=training --cov-report=html

# Skip GPU tests (CPU environment)
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
| Integration Tests | 30% | pytest + GCS/RabbitMQ mocks |
| GPU Tests | 10% | pytest (requires GPU) |

**Test Fixtures**: `tests/conftest.py`
**Coverage Goal**: 70%

---

## Deployment

### Production Checklist (GCP)

**GPU Server: Google Compute Engine (GCE)**

- [ ] **Create GCE VM Instance**
  - **머신 타입**: n2d-standard-4 또는 유사 사양
  - **GPU**: NVIDIA L4 (24GB VRAM) 또는 T4 (16GB VRAM)
  - **부팅 디스크**: Deep Learning on Linux 이미지 또는 CUDA 11.8+ 드라이버가 설치된 Ubuntu/Debian
  - **프로비저닝 모델**: **Spot(선점형)** 으로 설정하여 비용 절감 (강력 추천)
  - **서비스 계정**: Storage 관련 권한(`Storage 객체 생성자/뷰어`)이 있는 서비스 계정 연결

- [ ] **Configure RabbitMQ connection**
  - `RABBITMQ_HOST=<RabbitMQ VM의 내부 IP>`
  - GCE 방화벽 규칙에서 RabbitMQ 포트(5672)에 대한 내부 트래픽 허용

- [ ] **Configure Cloud Storage bucket**
  - 학습 이미지, 모델 파일을 저장할 버킷 생성 (`stylelicense-media`, `stylelicense-models`)
  - VM에 연결된 서비스 계정에 해당 버킷 접근 권한 부여

- [ ] **Configure Backend API connection**
  - `BACKEND_API_URL=https://api.stylelicense.com` (Cloud Run Public URL)
  - `INTERNAL_API_TOKEN=<32-character-UUID>` (내부 인증용)

- [ ] GPU 메모리 프로파일링
- [ ] Configure logging (Cloud Logging)

### Running in Production

```bash
# Run with Docker on GCE (use GPU)
docker run --gpus all \
    -e RABBITMQ_HOST=10.128.0.5 \
    -e GCS_BUCKET_NAME=stylelicense-media \
    -e INTERNAL_API_TOKEN=$TOKEN \
    stylelicense/training-server:latest
```

---

## Monitoring

### Metrics to Monitor

- Training progress (epoch, loss)
- GPU memory usage
- GPU utilization
- RabbitMQ queue length
- Training success/failure rate
- Average training time (per style)

---

## References

### Essential Documents
- **[CODE_GUIDE.md](CODE_GUIDE.md)** - Code writing patterns and examples (must read before coding)
- **[PLAN.md](PLAN.md)** - Development task plan (check next task)

### Project Documents
- **[TECHSPEC.md](../../TECHSPEC.md)** - Overall system architecture
- **[docs/PATTERNS.md](../../docs/PATTERNS.md)** - Message format (RabbitMQ)

### External Documentation
- **Diffusers**: https://huggingface.co/docs/diffusers
- **PEFT (LoRA)**: https://huggingface.co/docs/peft
- **PyTorch**: https://pytorch.org/docs/stable/

---

## Troubleshooting

### Common Issues

**1. CUDA not available**
```bash
# Verify CUDA installation
nvidia-smi

# Check PyTorch CUDA version
python -c "import torch; print(torch.version.cuda)"
```

**2. RabbitMQ connection refused**
```bash
docker ps | grep rabbitmq
docker restart rabbitmq
```

**3. Out of memory**
```bash
# Reduce batch size (config.py)
# Enable gradient checkpointing
# Use mixed precision training (FP16)
```

---

## Support

- **GitHub Issues**: Bug reports and feature requests
- **Team Communication**: Slack #ai-training channel
- **Documentation**: [TECHSPEC.md](../../TECHSPEC.md)
