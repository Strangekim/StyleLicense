# Backend Application

## Overview

Django REST Framework 기반의 Style License API 서버입니다. 사용자 인증, 스타일 모델 관리, 이미지 생성 요청, 토큰 시스템, 커뮤니티 기능을 제공하며, RabbitMQ를 통해 AI 서버들과 비동기 통신합니다.

**핵심 역할:**
- RESTful API 제공 (9개 API 그룹)
- RabbitMQ Producer (학습/생성 태스크 전송)
- Webhook Receiver (AI 서버로부터 진행상황/결과 수신)
- PostgreSQL 데이터 관리
- 세션 기반 인증 (Google OAuth)

---

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Framework | Django | 5.x | Web framework |
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
│   ├── models/                 # Django models (13 models)
│   │   ├── user.py            # User, UserProfile
│   │   ├── token.py           # TokenPackage, TokenTransaction
│   │   ├── style.py           # StyleModel, TrainingDataset, TrainingImage
│   │   ├── generation.py      # GenerationRequest, GeneratedImage
│   │   ├── community.py       # CommunityPost, PostLike, Comment
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

비즈니스 로직을 View에서 분리하여 `services/` 디렉토리에 위치시킵니다.

```
View (HTTP Request/Response) 
  ↓
Service (Business Logic)
  ↓
Model (Data Access)
```

**주요 Service:**
- `TokenService`: 토큰 소비/환불 (원자성 보장)
- `RabbitMQService`: AI 서버로 태스크 전송
- `S3Service`: 이미지/모델 파일 업로드/다운로드
- `NotificationService`: 알림 생성/전송

### Data Flow

#### 1. 모델 학습 플로우
```
작가 → Frontend: 이미지 업로드
Frontend → Backend: POST /api/styles/
Backend → S3: 이미지 저장
Backend → RabbitMQ: 학습 작업 발행
RabbitMQ → Training Server: 작업 수신
Training Server: LoRA Fine-tuning
Training Server → Backend: PATCH /api/webhooks/training/progress
Backend → Frontend: 학습 진행률 폴링
Training Server → S3: 모델 파일 저장
Training Server → Backend: POST /api/webhooks/training/complete
Backend → NotificationService: 알림 생성
```

#### 2. 이미지 생성 플로우
```
사용자 → Frontend: 프롬프트 입력
Frontend → Backend: POST /api/generations/
Backend → TokenService: 토큰 차감
Backend → RabbitMQ: 생성 작업 발행
RabbitMQ → Inference Server: 작업 수신
Inference Server: 이미지 생성 + 서명 삽입
Inference Server → S3: 이미지 저장
Inference Server → Backend: POST /api/webhooks/inference/complete
Backend → Frontend: 이미지 URL 반환
```

---

## Development Setup

### Prerequisites
- Python 3.11+
- PostgreSQL 15.x
- RabbitMQ 3.12+

### Installation

```bash
# 1. Virtual environment 생성
cd apps/backend
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 2. Dependencies 설치
pip install -r requirements/development.txt

# 3. 환경변수 설정
cp .env.example .env
# .env 파일 수정 (DATABASE_URL, RABBITMQ_HOST, AWS_* 등)

# 4. Database 마이그레이션
python manage.py migrate

# 5. 슈퍼유저 생성 (선택사항)
python manage.py createsuperuser

# 6. 개발 서버 실행
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

# AWS S3
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_STORAGE_BUCKET_NAME=stylelicense-media
AWS_S3_REGION_NAME=ap-northeast-2

# OAuth
GOOGLE_CLIENT_ID=your_client_id
GOOGLE_CLIENT_SECRET=your_client_secret

# Security
SECRET_KEY=your_django_secret_key
INTERNAL_API_TOKEN=your_internal_token  # AI 서버 webhook 인증용

# CORS
CORS_ALLOWED_ORIGINS=http://localhost:5173
```

---

## Development Workflow

### Running Tests

```bash
# 전체 테스트 실행
pytest

# Coverage 리포트
pytest --cov=app --cov-report=html

# 특정 마커만 실행
pytest -m "unit"  # 유닛 테스트만
pytest -m "integration"  # 통합 테스트만
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
# 마이그레이션 파일 생성
python manage.py makemigrations

# 마이그레이션 적용
python manage.py migrate

# 마이그레이션 롤백
python manage.py migrate app 0002  # 0002로 롤백
```

---

## API Documentation

전체 API 명세는 **[docs/API.md](../../docs/API.md)** 참조.

**주요 엔드포인트 그룹:**
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

전체 스키마는 **[docs/database/README.md](../../docs/database/README.md)** 참조.

**주요 모델 (13개):**
- **Auth**: User, UserProfile
- **Token**: TokenPackage, TokenTransaction
- **Style**: StyleModel, TrainingDataset, TrainingImage
- **Generation**: GenerationRequest, GeneratedImage
- **Community**: CommunityPost, PostLike, Comment
- **System**: Notification

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
- [ ] `ALLOWED_HOSTS` 설정 (도메인 추가: stylelicense.com)
- [ ] **로컬 PostgreSQL 15.x 설치 및 연결 설정**
  - `sudo apt install postgresql-15`
  - 데이터베이스 생성: `createdb stylelicense_db`
  - `DATABASE_URL=postgresql://user:pass@localhost:5432/stylelicense_db`
- [ ] **RabbitMQ Docker 설정**
  - `docker run -d --name rabbitmq -p 5672:5672 -p 15672:15672 rabbitmq:3-management`
  - `RABBITMQ_HOST=localhost`
  - Management UI는 SSH 터널로만 접근
- [ ] S3 버킷 설정 및 IAM 권한 확인 (**EC2 IAM Role 사용**)
  - EC2에 S3 Full Access IAM Role 부여
  - 학습 이미지: Private Bucket
  - 생성 이미지: Public Bucket
- [ ] `SECRET_KEY` 환경변수로 관리 (32자 이상 랜덤 문자열)
- [ ] **Nginx 설정**
  - Reverse Proxy: Gunicorn (:8000) 프록시
  - Frontend 정적 파일 서빙 (/var/www/stylelicense/frontend/)
  - Django Static files 서빙 (/home/ubuntu/stylelicense/apps/backend/staticfiles/)
  - 설정 파일: `/etc/nginx/sites-available/stylelicense`
- [ ] **Let's Encrypt SSL 인증서 설정**
  - `sudo certbot --nginx -d stylelicense.com -d www.stylelicense.com`
  - 자동 갱신 확인: `sudo certbot renew --dry-run`
- [ ] **DNS 설정**
  - A 레코드: stylelicense.com → Backend EC2 Public IP
- [ ] Static files 수집: `python manage.py collectstatic --noinput`
- [ ] Gunicorn/uWSGI 설정 (workers: CPU 코어 * 2 + 1)
- [ ] Sentry 에러 모니터링 (`SENTRY_DSN` 환경변수)

### Running in Production

```bash
# Gunicorn으로 실행
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

- API 응답 시간 (P50, P95, P99)
- 에러 비율 (4xx, 5xx)
- Database 쿼리 시간
- RabbitMQ 큐 길이
- CPU/메모리 사용률

---

## References

### 필수 문서
- **[CODE_GUIDE.md](CODE_GUIDE.md)** - 코드 작성 패턴 및 예제 (코드 작성 전 필독)
- **[PLAN.md](PLAN.md)** - 개발 작업 계획 (다음 작업 확인)
- **[docs/API.md](../../docs/API.md)** - 전체 API 명세
- **[docs/database/README.md](../../docs/database/README.md)** - DB 스키마

### 프로젝트 문서
- **[TECHSPEC.md](../../TECHSPEC.md)** - 전체 시스템 아키텍처
- **[docs/PATTERNS.md](../../docs/PATTERNS.md)** - 공통 코드 패턴
- **[docs/SECURITY.md](../../docs/SECURITY.md)** - 보안 정책

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
# PostgreSQL로 전환 권장
# .env에서 DATABASE_URL 수정
```

---

## Support

- **GitHub Issues**: 버그 리포트 및 기능 제안
- **Team Communication**: Slack #backend 채널
- **Documentation**: [TECHSPEC.md](../../TECHSPEC.md)