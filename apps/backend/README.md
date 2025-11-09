# Backend Application

## Overview

Style License API server based on Django REST Framework. Provides user authentication, style model management, image generation requests, token system, and community features, communicating asynchronously with AI servers via RabbitMQ.

**Core Responsibilities:**
- Provide RESTful API (9 API groups)
- RabbitMQ Producer (send training/generation tasks)
- Webhook Receiver (receive progress/results from AI servers)
- PostgreSQL data management
- Session-based authentication (Google OAuth)

---

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Framework | Django | 4.2 | Web framework (LTS) |
| API | Django REST Framework | 3.14+ | REST API |
| Database | PostgreSQL | 15.x | Primary database |
| Message Queue | RabbitMQ (pika) | 1.3+ | Async task queue |
| Authentication | django-allauth | 0.57+ | OAuth2 (Google) |
| Storage | Google Cloud Storage (google-cloud-storage) | 2.14+ | Image/model storage |
| Testing | pytest, pytest-django | 8.0+, 4.7+ | Unit/integration tests |
| Code Quality | black, pylint | 23.12+, 3.0+ | Formatting, linting |

---

## Directory Structure

```
apps/backend/
├── manage.py                    # Django CLI entry point
├── config/                      # Project settings
│   ├── settings/
│   │   ├── base.py             # Common settings
│   │   ├── development.py      # Local dev settings
│   │   └── production.py       # Production settings
│   ├── urls.py                 # Root URL configuration
│   └── wsgi.py                 # WSGI entry point
│
├── app/                        # Main application
│   ├── models/                 # Django models
│   │   ├── user.py            # User, Artist
│   │   ├── token.py           # Transaction, Purchase
│   │   ├── style.py           # Style, Artwork
│   │   ├── generation.py      # Generation
│   │   ├── community.py       # Follow, Like, Comment
│   │   ├── tagging.py         # Tag, StyleTag, ArtworkTag, GenerationTag
│   │   └── notification.py    # Notification
│   │
│   ├── serializers/           # DRF Serializers
│   │   ├── user.py
│   │   ├── token.py
│   │   ├── style.py
│   │   ├── generation.py
│   │   ├── community.py
│   │   └── notification.py
│   │
│   ├── views/                 # DRF ViewSets
│   │   ├── auth.py            # Login, Logout, Session check
│   │   ├── user.py            # UserViewSet
│   │   ├── token.py           # TokenViewSet
│   │   ├── style.py           # StyleViewSet
│   │   ├── generation.py      # GenerationViewSet
│   │   ├── community.py       # CommunityViewSet, LikeView, CommentView
│   │   ├── search.py          # SearchView
│   │   ├── notification.py    # NotificationViewSet
│   │   └── webhook.py         # WebhookView (AI server callbacks)
│   │
│   ├── services/              # Business logic layer
│   │   ├── token_service.py   # Token operations
│   │   ├── rabbitmq_service.py # Message queue operations
│   │   ├── gcs_service.py       # Storage operations
│   │   └── notification_service.py # Notification operations
│   │
│   ├── permissions/           # Custom DRF permissions
│   ├── pagination/            # Custom pagination
│   ├── middleware/            # Custom middleware
│   ├── migrations/            # Database migrations
│   └── tests/                 # Test suite
│
├── requirements/              # Python dependencies
│   ├── base.txt
│   ├── development.txt
│   └── production.txt
│
├── pytest.ini                # pytest configuration
├── .pylintrc                 # pylint configuration
├── PLAN.md                   # Development task plan
├── CODE_GUIDE.md             # Code patterns & conventions
└── README.md                 # This file
```

---

## Architecture

### Service Layer Pattern

Business logic is separated from Views and placed in the `services/` directory.

```
View (HTTP Request/Response)
  ↓
Service (Business Logic)
  ↓
Model (Data Access)
```

**Main Services:**
- `TokenService`: Token consumption/refund (atomicity guaranteed)
- `RabbitMQService`: Send tasks to AI servers
- `GCSService`: Image/model file upload/download to Google Cloud Storage
- `NotificationService`: Notification creation/delivery

### Data Flow

#### 1. Model Training Flow
```
Artist → Frontend: Upload images
Frontend → Backend(Cloud Run): POST /api/styles/
Backend → Cloud Storage: Store images
Backend → RabbitMQ: Publish training task
RabbitMQ → Training Server: Receive task
Training Server: LoRA Fine-tuning
Training Server → Backend(Cloud Run): PATCH /api/webhooks/training/progress
Backend → Frontend: Poll training progress
Training Server → Cloud Storage: Store model file
Training Server → Backend(Cloud Run): POST /api/webhooks/training/complete
Backend → NotificationService: Create notification
```

#### 2. Image Generation Flow
```
User → Frontend: Enter prompt
Frontend → Backend(Cloud Run): POST /api/generations/
Backend → TokenService: Deduct tokens
Backend → RabbitMQ: Publish generation task
RabbitMQ → Inference Server: Receive task
Inference Server: Generate image + Insert signature
Inference Server → Cloud Storage: Store image
Inference Server → Backend(Cloud Run): POST /api/webhooks/inference/complete
Backend → Frontend: Return image URL
```

---

## Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15.x
- RabbitMQ 3.12+

### Installation

```bash
# 1. Create virtual environment
cd apps/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Install dependencies
pip install -r requirements/development.txt

# 3. Set environment variables
cp .env.example .env
# Edit .env file (DATABASE_URL, RABBITMQ_HOST, etc.)

# 4. Run database migrations
python manage.py migrate

# 5. Create superuser (optional)
python manage.py createsuperuser

# 6. Run development server
python manage.py runserver
```

### Environment Variables

```bash
# Database (Cloud SQL)
# Cloud Run 환경에서는 Cloud SQL 연결 설정을 통해 자동으로 주입됩니다.
# 로컬 개발 시에는 Cloud SQL Auth Proxy 또는 로컬 DB 주소를 사용합니다.
DATABASE_URL=postgresql://user:pass@localhost:5432/stylelicense

# RabbitMQ (on GCE)
# 운영 환경에서는 GCE VM의 내부 IP를 사용합니다.
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

# Google Cloud Storage
# Cloud Run 서비스 계정에 Storage 권한을 부여하므로, 키가 필요 없습니다.
GCS_BUCKET_NAME=stylelicense-media

# OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# Security
SECRET_KEY=your_django_secret_key
INTERNAL_API_TOKEN=your_internal_token  # For AI server webhook authentication

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173,https://your-frontend-domain.com
```

---

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Coverage report
pytest --cov=app --cov-report=html

# Run specific markers only
pytest -m "unit"  # Unit tests only
pytest -m "integration"  # Integration tests only
```

### Code Quality

```bash
# Format
black app/

# Lint
pylint app/
```

### Migrations

```bash
# Create migration files
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Rollback migrations
python manage.py migrate app 0002  # Rollback to 0002
```

---

## API Documentation

For complete API specification, refer to **[docs/API.md](../../docs/API.md)**.

---

## Database Schema

For complete schema, refer to **[docs/database/README.md](../../docs/database/README.md)**.

---

## Testing Strategy

### Test Types

| Type | Coverage | Tools |
|------|----------|-------|
| Unit Tests | 70% | pytest, pytest-django |
| Integration Tests | 20% | DRF APIClient |
| Performance Tests | 10% | pytest-benchmark |

**Test Fixtures**: `app/tests/conftest.py`
**Coverage Goal**: 80%

---

## Deployment (GCP)

### Production Deployment to Cloud Run

이 Django 백엔드 애플리케이션은 컨테이너화되어 **Google Cloud Run**으로 배포됩니다. Cloud Run은 서버리스 환경으로, 트래픽에 따라 자동으로 확장/축소되며 별도의 웹 서버(Nginx, Gunicorn) 설정이 필요 없습니다.

### Prerequisites
- `gcloud` CLI 설치 및 인증
- Google Artifact Registry에 Docker 이미지 Push

### Deployment Steps

1.  **Dockerfile 준비**: 프로젝트 루트의 `Dockerfile`이 컨테이너를 빌드하는 데 사용됩니다. Gunicorn이 Dockerfile 내에서 실행되도록 설정합니다.

2.  **Docker 이미지 빌드 및 Push**:
    ```bash
    # GCP Project ID 설정
    export PROJECT_ID=your-gcp-project-id
    export REPO_NAME=stylelicense
    export IMAGE_NAME=backend

    # Artifact Registry에 이미지 Push
    gcloud builds submit --tag gcr.io/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:latest .
    ```

3.  **Cloud Run 배포**:
    `gcloud run deploy` 명령어를 사용하여 컨테이너를 배포합니다. 이 과정에서 필요한 환경 변수와 Cloud SQL 연결을 설정합니다.

    ```bash
    gcloud run deploy stylelicense-backend \
      --image gcr.io/$PROJECT_ID/$REPO_NAME/$IMAGE_NAME:latest \
      --platform managed \
      --region asia-northeast3 \
      --allow-unauthenticated \
      --add-cloudsql-instances [INSTANCE_CONNECTION_NAME] \
      --set-env-vars="SECRET_KEY=your_secret_key,GCS_BUCKET_NAME=stylelicense-media,RABBITMQ_HOST=10.x.x.x"
    ```

### 주요 설정
- **데이터베이스 연결**: `--add-cloudsql-instances` 플래그를 사용하여 Cloud SQL Auth Proxy를 자동으로 활성화하고 안전하게 DB에 연결합니다. `DATABASE_URL`은 Cloud Run 환경에 맞게 설정됩니다.
- **환경 변수**: `--set-env-vars` 플래그를 사용하여 민감하지 않은 환경 변수를 설정합니다. 민감한 정보(API 키 등)는 **Secret Manager**를 사용하는 것이 권장됩니다.
- **자동 확장**: Cloud Run은 요청 수에 따라 인스턴스 수를 0에서 설정된 최대값까지 자동으로 조절합니다.

---

## Monitoring

### Health Check Endpoint

```
GET /api/health
```

### Metrics to Monitor

- API response time (P50, P95, P99)
- Error rate (4xx, 5xx)
- Database query time
- RabbitMQ queue length
- CPU/memory usage

---

## References

### Essential Documents
- **[CODE_GUIDE.md](CODE_GUIDE.md)** - Code writing patterns and examples (must read before coding)
- **[PLAN.md](PLAN.md)** - Development task plan (check next task)
- **[docs/API.md](../../docs/API.md)** - Complete API specification
- **[docs/database/README.md](../../docs/database/README.md)** - DB schema

### Project Documents
- **[TECHSPEC.md](../../TECHSPEC.md)** - Overall system architecture
- **[docs/PATTERNS.md](../../docs/PATTERNS.md)** - Common code patterns
- **[DOCKER.md](../../DOCKER.md)** - Docker setup and deployment guide

---

## Troubleshooting

### Common Issues

**1. Migration conflicts**
```bash
python manage.py makemigrations --merge
```

**2. RabbitMQ connection refused**
```bash
docker ps | grep rabbitmq
docker restart rabbitmq
```

**3. Database locked**
```bash
# Switch to PostgreSQL recommended
# Modify DATABASE_URL in .env
```

---

## Support

- **GitHub Issues**: Bug reports and feature requests
- **Team Communication**: Slack #backend channel
- **Documentation**: [TECHSPEC.md](../../TECHSPEC.md)
