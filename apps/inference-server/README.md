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

Pipeline that combines user prompts with LoRA style to generate images.

```
RabbitMQ Queue
  ↓
Generation Consumer (receive message)
  ↓
S3 Service (download LoRA weights)
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
S3 Service (upload image)
  ↓
Webhook Service (notify generation complete)
```

**Main Components:**
- `GenerationConsumer`: Receive generation tasks from RabbitMQ (max 10 simultaneous)
- `ImageGenerator`: Stable Diffusion v1.5 + LoRA inference
- `WatermarkInserter`: PIL-based artist signature watermark insertion
- `S3Service`: Download/upload LoRA models/images
- `WebhookService`: Send progress/results to Backend API

### Data Flow

#### Image Generation Flow
```
Backend → RabbitMQ: Publish generation task
RabbitMQ → Inference Server: Receive task
Inference Server → S3: Download LoRA weights
Inference Server: Stable Diffusion inference (50 steps)
Inference Server → Backend: Report progress (0%, 25%, 50%, 75%, 90%, PATCH /api/webhooks/inference/progress)
Inference Server: Automatically insert artist signature (watermark)
Inference Server → S3: Upload generated image (.png)
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
- GPU Memory: Minimum 6GB VRAM (RTX 3060 or higher recommended)
- RabbitMQ 3.12+
- AWS S3: Bucket and IAM permissions

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

# AWS S3 (IAM User Access Key)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_STORAGE_BUCKET_NAME=stylelicense-media
AWS_S3_REGION_NAME=ap-northeast-2

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
| Integration Tests | 30% | pytest + S3/RabbitMQ mocks |
| GPU Tests | 10% | pytest (requires GPU) |

**Test Fixtures**: `tests/conftest.py`
**Coverage Goal**: 70%

---

## Deployment

### Production Checklist

**GPU Server: RunPod RTX 4090 24GB**

- [ ] **Create RunPod GPU Pod**
  - GPU: RTX 4090 (24GB VRAM)
  - Template: Custom Docker Image
  - Image: `<registry>/stylelicense-inference:latest`
- [ ] Use Docker image with CUDA 11.8+
- [ ] **Configure RabbitMQ connection**
  - `RABBITMQ_HOST=<Backend-EC2-Public-IP>`
  - Expose Backend EC2's RabbitMQ port (5672) publicly or use VPN
  - Firewall: Allow RunPod Pod IP in Backend EC2 Security Group
- [ ] **Configure S3 bucket**
  - Generated images: Public Bucket (`stylelicense-generations`)
  - **Set AWS Access Key environment variables** (for S3 access from RunPod Pod)
- [ ] **Configure Backend API connection**
  - `BACKEND_API_URL=https://api.stylelicense.com` (use domain)
  - `INTERNAL_API_TOKEN=<32-character-UUID>` (for webhook authentication)
  - Backend EC2 Security Group: Allow port 443 (RunPod IP or all)
- [ ] GPU memory profiling (within 24GB)
- [ ] Configure logging (RunPod console or CloudWatch)
- [ ] Install font files (for watermark - include in Docker image)
- [ ] Set concurrent generation limit (`MAX_CONCURRENT_GENERATIONS=10`)
- [ ] Configure log collection (CloudWatch, Sentry)
- [ ] Establish model caching strategy

### Running in Production

```bash
# Run with Docker (use GPU)
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
