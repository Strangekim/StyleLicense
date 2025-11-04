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

Pipeline for fine-tuning Stable Diffusion model with user images.

```
RabbitMQ Queue
  ↓
Training Consumer (receive message)
  ↓
S3 Service (download training images)
  ↓
LoRA Trainer (train model)
  ├─ Prepare dataset
  ├─ Apply LoRA config
  ├─ Execute training loop
  ├─ Save checkpoint (every 10 epochs)
  └─ Report progress (every 30 seconds)
  ↓
S3 Service (upload model weights)
  ↓
Webhook Service (notify training complete)
```

**Main Components:**
- `TrainingConsumer`: Receive training tasks from RabbitMQ
- `LoRATrainer`: Stable Diffusion v1.5 + LoRA training
- `S3Service`: Download/upload images/models
- `WebhookService`: Send progress/results to Backend API

### Data Flow

#### Model Training Flow
```
Backend → RabbitMQ: Publish training task
RabbitMQ → Training Server: Receive task
Training Server → S3: Download images (10-30 images)
Training Server: LoRA Fine-tuning (100-500 epochs)
Training Server → Backend: Report progress (every 30 seconds, PATCH /api/webhooks/training/progress)
Training Server → S3: Save checkpoints (every 10 epochs)
Training Server → S3: Upload final model (.safetensors)
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
- GPU Memory: Minimum 8GB VRAM (RTX 3060 or higher recommended)
- RabbitMQ 3.12+
- AWS S3: Bucket and IAM permissions

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
  - Image: `<registry>/stylelicense-training:latest`
- [ ] Use Docker image with CUDA 11.8+
- [ ] **Configure RabbitMQ connection**
  - `RABBITMQ_HOST=<Backend-EC2-Public-IP>`
  - Expose Backend EC2's RabbitMQ port (5672) publicly or use VPN
  - Firewall: Allow RunPod Pod IP in Backend EC2 Security Group
- [ ] **Configure S3 bucket**
  - Training images: Private Bucket (`stylelicense-training-data`)
  - Model files: Private Bucket (`stylelicense-models`)
  - **Set AWS Access Key environment variables** (for S3 access from RunPod Pod)
- [ ] **Configure Backend API connection**
  - `BACKEND_API_URL=https://api.stylelicense.com` (use domain)
  - `INTERNAL_API_TOKEN=<32-character-UUID>` (for webhook authentication)
  - Backend EC2 Security Group: Allow port 443 (RunPod IP or all)
- [ ] GPU memory profiling (within 24GB)
- [ ] Configure logging (RunPod console or CloudWatch)
- [ ] Set checkpoint save path
- [ ] Configure log collection (CloudWatch, Sentry)

### Running in Production

```bash
# Run with Docker (use GPU)
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
