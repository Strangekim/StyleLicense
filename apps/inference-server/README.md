# Inference Server

## Overview

Stable Diffusion-based image generation server. Receives generation requests from RabbitMQ, generates images using user-trained LoRA style models, inserts watermarks, and uploads to S3.

**Core Responsibilities:**
- RabbitMQ Consumer (`image_generation` queue)
- Stable Diffusion image generation (apply LoRA weights)
- Watermark (signature) insertion
- Batch processing (max 10 simultaneous generations)
- Generation progress reporting
- Send complete/failed webhooks

---

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Language | Python | 3.11+ | Core language |
| ML Framework | PyTorch | 2.1+ | Deep learning |
| Diffusion | Diffusers (Hugging Face) | 0.25+ | Stable Diffusion inference |
| Image Processing | Pillow (PIL) | 10.1+ | Watermark insertion |
| Message Queue | RabbitMQ (pika) | 1.3+ | Task queue consumer |
| Storage | Google Cloud Storage (google-cloud-storage) | 2.14+ | Image storage |
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

Pipeline that combines user prompts with LoRA style to generate images.

```
RabbitMQ Queue
  ↓
Generation Consumer (receive message)
  ↓
Cloud Storage Service (download LoRA weights)
  ↓
Image Generator (generate image)
  ├─ Load Stable Diffusion pipeline
  ├─ Apply LoRA weights
  ├─ Generate image (50 steps)
  └─ Report progress
  ↓
Watermark Inserter (insert watermark)
  ├─ Add artist signature
  ├─ Set position/opacity
  └─ Composite image
  ↓
Cloud Storage Service (upload image)
  ↓
Webhook Service (notify generation complete)
```

**Main Components:**
- `GenerationConsumer`: Receive generation tasks from RabbitMQ (max 10 simultaneous)
- `ImageGenerator`: Stable Diffusion v1.5 + LoRA inference
- `WatermarkInserter`: PIL-based artist signature watermark insertion
- `GCSService`: Download/upload LoRA models/images from/to Google Cloud Storage
- `WebhookService`: Send progress/results to Backend API

### Data Flow

#### Image Generation Flow
```
Backend → RabbitMQ: Publish generation task
RabbitMQ → Inference Server: Receive task
Inference Server → Cloud Storage: Download LoRA weights
Inference Server: Stable Diffusion inference (50 steps)
Inference Server → Backend: Report progress (10%, 25%, 50%, 75%, 90%, PATCH /api/webhooks/inference/progress)
Inference Server: Automatically insert artist signature (watermark)
Inference Server → Cloud Storage: Upload generated image (.png)
Inference Server → Backend: POST /api/webhooks/inference/complete
Backend → Frontend: Return image URL
```

**Detailed API spec**: [docs/API.md#10-webhook-api](../../docs/API.md#10-webhook-api)

**Generation parameters (based on TECHSPEC.md and PLAN.md):**
- Base Model: Stable Diffusion v1.5
- Sampling Steps: 50
- Guidance Scale: 7.5
- Image Size: 512x512
- Scheduler: DPM-Solver++ (fast inference)
- Batch Size: 1-4 (simultaneous generation)

---

## Development Setup

### Prerequisites
- Python 3.11+
- CUDA 11.8+ (NVIDIA GPU required)
- GPU Memory: Minimum 6GB VRAM (NVIDIA T4 or higher recommended)
- RabbitMQ 3.12+
- Google Cloud Storage: Bucket and IAM permissions

### Installation

```bash
# 1. Create virtual environment
cd apps/inference-server
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

# Batch Processing
MAX_CONCURRENT_GENERATIONS=10

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
pytest --cov=inference --cov-report=html

# Skip GPU tests (CPU environment)
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
  - **GPU**: **NVIDIA T4 (16GB VRAM)** - 추론에 가장 비용 효율적
  - **부팅 디스크**: Deep Learning on Linux 이미지 또는 CUDA 11.8+ 드라이버가 설치된 Ubuntu/Debian
  - **프로비저닝 모델**: **Standard(표준)**. 24/7 운영을 위해 **1년 약정 사용 할인(CUD)** 적용하여 비용 절감.
  - **서비스 계정**: Storage 관련 권한(`Storage 객체 생성자/뷰어`)이 있는 서비스 계정 연결

- [ ] **Configure RabbitMQ connection**
  - `RABBITMQ_HOST=<RabbitMQ VM의 내부 IP>`
  - GCE 방화벽 규칙에서 RabbitMQ 포트(5672)에 대한 내부 트래픽 허용

- [ ] **Configure Cloud Storage bucket**
  - 생성된 이미지를 저장할 버킷 생성 (`stylelicense-generations`)
  - LoRA 모델이 저장된 버킷 (`stylelicense-models`)
  - VM에 연결된 서비스 계정에 해당 버킷 접근 권한 부여

- [ ] **Configure Backend API connection**
  - `BACKEND_API_URL=https://api.stylelicense.com` (Cloud Run Public URL)
  - `INTERNAL_API_TOKEN=<32-character-UUID>` (내부 인증용)

- [ ] GPU 메모리 프로파일링
- [ ] Configure logging (Cloud Logging)
- [ ] Install font files (for watermark - include in Docker image)
- [ ] Set concurrent generation limit (`MAX_CONCURRENT_GENERATIONS=10`)
- [ ] Establish model caching strategy

### Running in Production

```bash
# Run with Docker on GCE (use GPU)
docker run --gpus all \
    -e RABBITMQ_HOST=10.128.0.5 \
    -e GCS_BUCKET_NAME=stylelicense-media \
    -e INTERNAL_API_TOKEN=$TOKEN \
    -e MAX_CONCURRENT_GENERATIONS=10 \
    stylelicense/inference-server:latest
```

---

## Monitoring

### Metrics to Monitor

- Generation time (per image)
- GPU memory usage
- GPU utilization
- RabbitMQ queue length
- Generation success/failure rate
- Average generation time (steps per second)

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
- **Stable Diffusion**: https://github.com/CompVis/stable-diffusion
- **PyTorch**: https://pytorch.org/docs/stable/
- **Pillow (PIL)**: https://pillow.readthedocs.io/

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

**2. Out of memory**
```bash
# Enable attention slicing (config.py)
# Reduce steps (30 steps)
# Set batch size to 1
```

**3. Font not found (watermark)**
```bash
# Debian/Ubuntu
apt-get install fonts-dejavu-core

# Alpine
apk add ttf-dejavu
```

**4. Slow generation**
```bash
# Enable xFormers
# Use DPM-Solver++ scheduler (default)
# Enable model caching
```

---

## Support

- **GitHub Issues**: Bug reports and feature requests
- **Team Communication**: Slack #ai-inference channel
- **Documentation**: [TECHSPEC.md](../../TECHSPEC.md)
