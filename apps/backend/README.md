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
| Storage | AWS S3 (boto3) | 1.34+ | Image/model storage |
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
│   │   ├── s3_service.py      # Storage operations
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
- `S3Service`: Image/model file upload/download
- `NotificationService`: Notification creation/delivery

### Data Flow

#### 1. Model Training Flow
```
Artist → Frontend: Upload images
Frontend → Backend: POST /api/styles/
Backend → S3: Store images
Backend → RabbitMQ: Publish training task
RabbitMQ → Training Server: Receive task
Training Server: LoRA Fine-tuning
Training Server → Backend: PATCH /api/webhooks/training/progress
Backend → Frontend: Poll training progress
Training Server → S3: Store model file
Training Server → Backend: POST /api/webhooks/training/complete
Backend → NotificationService: Create notification
```

#### 2. Image Generation Flow
```
User → Frontend: Enter prompt
Frontend → Backend: POST /api/generations/
Backend → TokenService: Deduct tokens
Backend → RabbitMQ: Publish generation task
RabbitMQ → Inference Server: Receive task
Inference Server: Generate image + Insert signature
Inference Server → S3: Store image
Inference Server → Backend: POST /api/webhooks/inference/complete
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
# Edit .env file (DATABASE_URL, RABBITMQ_HOST, AWS_* etc.)

# 4. Run database migrations
python manage.py migrate

# 5. Create superuser (optional)
python manage.py createsuperuser

# 6. Run development server
python manage.py runserver
```

### Environment Variables

```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/stylelicense

# RabbitMQ
RABBITMQ_HOST=localhost
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

# AWS S3 (for local development)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_STORAGE_BUCKET_NAME=stylelicense-media
AWS_S3_REGION_NAME=ap-northeast-2

# Production: Use EC2 IAM Role (no environment variables needed)

# OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# Security
SECRET_KEY=your_django_secret_key
INTERNAL_API_TOKEN=your_internal_token  # For AI server webhook authentication

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173
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

**Main Endpoint Groups:**
- **Authentication**: `/api/auth/google/login`, `/api/auth/me`, `/api/auth/logout`
- **User**: `/api/users/:id`, `/api/users/me`, `/api/users/me/upgrade-to-artist`
- **Token**: `/api/tokens/balance`, `/api/tokens/transactions`, `/api/tokens/purchase`
- **Style**: `/api/styles`, `/api/styles/:id`, `/api/styles/me`
- **Generation**: `/api/generations`, `/api/generations/:id`, `/api/generations/feed`, `/api/generations/me`
- **Social**: `/api/users/:id/follow`, `/api/generations/:id/like`, `/api/generations/:id/comments`
- **Search**: `/api/search` (query parameter: `?type=styles|artists|all`)
- **Notification**: `/api/notifications`, `/api/notifications/:id/read`, `/api/notifications/read-all`
- **Webhook** (Internal): `/api/webhooks/training/*`, `/api/webhooks/inference/*`

---

## Database Schema

For complete schema, refer to **[docs/database/README.md](../../docs/database/README.md)**.

**Main Models (15 tables):**
- **Auth**: users, artists
- **Token**: transactions, purchases
- **Style**: styles, artworks
- **Generation**: generations
- **Community**: follows, likes, comments
- **Tagging**: tags, style_tags, artwork_tags, generation_tags
- **System**: notifications

**Important Field Descriptions**:
- `users.role`: 'user' or 'artist' (artist permission distinction)
- `styles.generation_cost_tokens`: Token cost per image
- `transactions.transaction_type`: Transaction type ('purchase', 'generation', 'withdrawal', 'transfer')

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

## Deployment

### Production Checklist

- [ ] `DEBUG = False`
- [ ] Set `ALLOWED_HOSTS` (add domain: stylelicense.com)
- [ ] **PostgreSQL 15.x setup (Docker recommended)**
  - **Using Docker (recommended)**:
    ```bash
    docker run -d --name postgres \
      -e POSTGRES_PASSWORD=your_password \
      -v /var/lib/postgresql/data:/var/lib/postgresql/data \
      -p 5432:5432 postgres:15
    ```
  - **Local installation (alternative)**:
    ```bash
    sudo apt install postgresql-15
    createdb stylelicense_db
    ```
  - `DATABASE_URL=postgresql://user:pass@localhost:5432/stylelicense_db`
- [ ] **RabbitMQ Docker setup**
  - `docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management`
  - `RABBITMQ_HOST=localhost`
  - Management UI accessible only via SSH tunnel
- [ ] S3 bucket setup and IAM permissions (**Use EC2 IAM Role**)
  - Assign S3 Full Access IAM Role to EC2
  - Training images: Private Bucket
  - Generated images: Public Bucket
- [ ] Manage `SECRET_KEY` via environment variable (32+ random characters)
- [ ] **Nginx configuration**
  - Reverse Proxy: Gunicorn (:8000) proxy
  - Serve Frontend static files (/var/www/stylelicense/frontend/)
  - Serve Django Static files (/home/ubuntu/stylelicense/apps/backend/staticfiles/)
  - Config file: `/etc/nginx/sites-available/stylelicense`
- [ ] **Let's Encrypt SSL certificate setup**
  - `sudo certbot --nginx -d stylelicense.com -d www.stylelicense.com`
  - Verify auto-renewal: `sudo certbot renew --dry-run`
- [ ] **DNS configuration**
  - A record: stylelicense.com → Backend EC2 Public IP
- [ ] Collect static files: `python manage.py collectstatic --noinput`
- [ ] Gunicorn/uWSGI configuration (workers: CPU cores * 2 + 1)
- [ ] Sentry error monitoring (`SENTRY_DSN` environment variable)

### Running in Production

```bash
# Run with Gunicorn
gunicorn config.wsgi:application \
    --bind 0.0.0.0:8000 \
    --workers 4 \
    --timeout 120
```

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
