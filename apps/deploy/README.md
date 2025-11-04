# Deploy Project

## Overview

Style License 프로젝트의 **EC2 배포 전용 독립 프로젝트**입니다. Backend 코드 전문과 Frontend 빌드 결과물, 그리고 모든 설정 파일을 포함하여 EC2에서 이 폴더만 clone/pull하면 전체 스택을 실행할 수 있습니다.

**핵심 역할:**
- **Backend 전문**: Django 코드 (`apps/backend/` 전체)
- **Frontend 빌드 결과물**: Vite 빌드 산출물 (`frontend/dist/`)
- **인프라 설정**: Docker Compose, Nginx, PostgreSQL, RabbitMQ 설정
- **배포 스크립트**: `deploy.sh` 반자동 배포 스크립트
- **환경변수 관리**: `.env.example` 템플릿

## 폴더 구조

```
apps/deploy/
├── backend/                    # Backend 전문 (Django 코드)
│   ├── app/                   # Django 애플리케이션
│   ├── config/                # Django 설정
│   ├── manage.py
│   └── requirements.txt
│
├── frontend/                   # Frontend 빌드 결과물
│   └── dist/                  # Vite 빌드 산출물 (index.html, assets/)
│
├── docker-compose.yml          # Docker Compose 설정
├── nginx.conf                 # Nginx 설정 파일
├── .env.example               # 환경변수 템플릿
├── deploy.sh                  # 배포 스크립트
├── scripts/                   # 유틸리티 스크립트
│   ├── setup.sh              # 초기 설정
│   └── backup.sh             # DB 백업
└── README.md                  # 이 파일
```

> **중요**: 이 폴더는 **배포 전용**입니다. 개발은 `apps/backend/`, `apps/frontend/`에서 하고, 변경사항을 이 폴더로 복사하여 배포합니다.

---

## Local Development Environment

### Docker Compose

전체 스택을 Docker Compose로 실행하여 로컬 개발 환경을 구성합니다.

#### 구성 서비스

```yaml
services:
  backend:        # Django REST API
  frontend:       # Vue 3 SPA
  training-server: # LoRA Fine-tuning Server (GPU 필요)
  inference-server: # Stable Diffusion Inference (GPU 필요)
  postgres:       # PostgreSQL 15
  rabbitmq:       # RabbitMQ 3 (Management UI 포함)
```

#### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- NVIDIA Docker (GPU 서버용)
  - Training-server, Inference-server 실행 시 필수
  - CUDA 11.8+ 지원

#### 실행 방법

```bash
# 1. 프로젝트 루트로 이동
cd /path/to/StyleLicense

# 2. 환경변수 설정
cp .env.example .env
# .env 파일 수정 (DATABASE_URL, RABBITMQ_HOST 등)

# 3. 전체 스택 실행
docker-compose up -d

# 4. 로그 확인
docker-compose logs -f backend

# 5. 종료
docker-compose down
```

#### GPU 서버 실행 (선택사항)

GPU가 없는 환경에서는 Training/Inference Server를 제외하고 실행:

```bash
# GPU 서버 제외하고 실행
docker-compose up -d backend frontend postgres rabbitmq

# GPU 서버만 실행 (NVIDIA GPU 필요)
docker-compose up -d training-server inference-server
```

#### 서비스 접근 포트

| 서비스 | 포트 | 설명 |
|--------|------|------|
| Backend | 8000 | Django REST API |
| Frontend | 5173 | Vue 3 Dev Server (Vite) |
| PostgreSQL | 5432 | Database |
| RabbitMQ | 5672 | AMQP |
| RabbitMQ Management | 15672 | 관리 UI (http://localhost:15672) |

**RabbitMQ 관리 UI 접속**:
- URL: http://localhost:15672
- ID: guest
- PW: guest

---

## Production Architecture

### AWS 인프라 구성

```
사용자 (브라우저)
  ↓ HTTPS (DNS: stylelicense.com)
  ↓
Backend EC2 (t3.medium)
  ├── Nginx (포트 80, 443)
  │   ├── SSL 종료 (Let's Encrypt)
  │   ├── Frontend 정적 파일 서빙
  │   └── Gunicorn Reverse Proxy
  ├── Django Backend (Gunicorn :8000)
  ├── PostgreSQL 15 (로컬 :5432)
  └── RabbitMQ (Docker :5672)
        ↓ (작업 큐)
        ↓
  RunPod GPU Pods (RTX 4090 24GB)
  ├── Training Server (1대)
  └── Inference Server (1대)
        ↓ Webhook (Public IP + INTERNAL_API_TOKEN)
        ↑
  AWS S3 (이미지/모델 파일 저장)
```

### 인스턴스 구성

| 서비스 | 인스턴스 타입 | 수량 | 설명 |
|--------|--------------|------|------|
| **Backend** | EC2 t3.medium | 1 | Django + Gunicorn + Nginx + PostgreSQL + RabbitMQ |
| **Frontend** | (Backend에 포함) | - | Nginx에서 정적 파일 서빙 |
| **Database** | PostgreSQL 15 (Docker) | 1 | Backend EC2에서 Docker 컨테이너로 실행 |
| **Queue** | RabbitMQ (Docker) | 1 | Backend EC2에 함께 실행 |
| **Training Server** | RunPod RTX 4090 24GB | 1 | LoRA Fine-tuning 전용 GPU Pod |
| **Inference Server** | RunPod RTX 4090 24GB | 1 | 이미지 생성 전용 GPU Pod |
| **Storage** | S3 | - | 이미지/모델 저장 (IAM Role/Access Key) |
| **DNS** | 별도 구매 예정 | - | 도메인 (예: stylelicense.com) |
| **SSL** | Let's Encrypt | - | Certbot 자동 갱신 |

### 네트워크 구성

- **Backend EC2 Security Group**:
  - Inbound: 80 (HTTP), 443 (HTTPS) - 전체 허용 (0.0.0.0/0)
  - Inbound: 22 (SSH) - 관리자 IP만 허용
  - Outbound: 전체 허용 (S3, RabbitMQ, RunPod 접근)

- **RunPod GPU Pods**:
  - Inbound: RabbitMQ 큐 소비 (Backend 연결)
  - Outbound: Backend Webhook 호출 (Public IP, HTTPS 443)
    - 방화벽: Backend 도메인으로만 통신
    - 인증: `Authorization: Bearer <INTERNAL_API_TOKEN>` 헤더
  - Outbound: S3 업로드 (AWS Access Key 사용)

- **DNS 설정**:
  - 도메인: stylelicense.com (예시)
  - A 레코드: Backend EC2 Public IP 지정
  - SSL: Let's Encrypt (Certbot 자동 발급 및 갱신)

- **PostgreSQL**:
  - 로컬 접근만 (localhost:5432)
  - 외부 접근 차단

- **RabbitMQ**:
  - Docker 컨테이너로 실행
  - Backend Django에서만 접근 (localhost:5672)
  - Management UI: localhost:15672 (SSH 터널로만 접근)

---

## Environment Variables

### Local Development (.env)

```bash
# Database
DATABASE_URL=postgresql://user:pass@postgres:5432/stylelicense

# RabbitMQ
RABBITMQ_HOST=rabbitmq
RABBITMQ_PORT=5672
RABBITMQ_USER=guest
RABBITMQ_PASS=guest

# AWS S3 (로컬 개발 시 선택사항)
AWS_ACCESS_KEY_ID=your_key
AWS_SECRET_ACCESS_KEY=your_secret
AWS_STORAGE_BUCKET_NAME=stylelicense-media
AWS_S3_REGION_NAME=ap-northeast-2

# Backend API
BACKEND_API_URL=http://backend:8000
INTERNAL_API_TOKEN=local-dev-token

# Frontend
VITE_API_BASE_URL=http://localhost:8000
```

### Production (AWS Systems Manager Parameter Store)

프로덕션 환경에서는 민감한 정보를 Parameter Store에 저장:

```bash
# 파라미터 저장 예시
aws ssm put-parameter \
  --name /stylelicense/prod/DATABASE_URL \
  --value "postgresql://..." \
  --type SecureString

# 애플리케이션에서 읽기
aws ssm get-parameter \
  --name /stylelicense/prod/DATABASE_URL \
  --with-decryption
```

**관리 대상**:
- DATABASE_URL (RDS 연결 문자열)
- SECRET_KEY (Django Secret Key)
- AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY
- INTERNAL_API_TOKEN (Webhook 인증 토큰)
- GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET (OAuth)

---

## Deployment Process

### 배포 방식

**당분간은 수동/반자동 배포를 사용합니다** (CI/CD는 향후 도입 예정)

#### 1. EC2 초기 설정

```bash
# 1. EC2 접속
ssh -i keypair.pem ubuntu@<ec2-public-ip>

# 2. 프로젝트 Clone
git clone <repository-url>
cd StyleLicense/apps/deploy

# 3. 초기 설정 스크립트 실행
chmod +x scripts/setup.sh
./scripts/setup.sh

# 4. 환경변수 설정
cp .env.example .env
nano .env  # 프로덕션 환경변수 입력

# 5. 초기 배포
chmod +x deploy.sh
./deploy.sh
```

#### 2. 코드 변경 시 배포

```bash
# EC2에서 실행
cd /path/to/StyleLicense/apps/deploy

# 1. 최신 코드 Pull
git pull origin main

# 2. 배포 스크립트 실행
./deploy.sh
```

### deploy.sh 스크립트 역할

`deploy.sh` 스크립트는 다음 작업을 자동으로 수행합니다:

```bash
#!/bin/bash
# 1. PostgreSQL 마이그레이션 실행
cd backend
python manage.py migrate

# 2. Django Static 파일 수집
python manage.py collectstatic --noinput

# 3. Frontend 빌드 파일 Nginx 디렉토리로 복사
cp -r frontend/dist/* /var/www/stylelicense/frontend/

# 4. Gunicorn 재시작
sudo systemctl restart gunicorn

# 5. RabbitMQ 상태 확인
docker ps | grep rabbitmq

# 6. Nginx 재시작
sudo systemctl reload nginx

# 7. Health Check
curl http://localhost:8000/api/health
```

### 배포 전 체크리스트

- [ ] Backend 변경사항이 있으면 `apps/deploy/backend/`로 복사 완료
- [ ] Frontend 변경사항이 있으면 `npm run build` 후 `apps/deploy/frontend/dist/`로 복사 완료
- [ ] `.env` 파일 프로덕션 환경변수 설정 완료
- [ ] PostgreSQL 백업 완료 (`./scripts/backup.sh`)
- [ ] 배포 전 로컬에서 테스트 완료

---

## CI/CD (향후 계획)

> **참고**: 현재는 수동 배포를 사용하며, 향후 GitHub Actions 또는 GitLab CI를 도입할 예정입니다.

향후 자동화 예정 항목:
- Backend 변경 시 자동 테스트 및 배포
- Frontend 빌드 및 배포 자동화
- RunPod GPU Pods 자동 업데이트
- Health Check 및 롤백 자동화

---

## Configuration Guide

### 1. PostgreSQL 설정 (Docker 사용)

**Docker로 PostgreSQL 실행 (권장)**:
```bash
# Docker 컨테이너로 PostgreSQL 실행
docker run -d \
  --name postgres \
  --restart always \
  -e POSTGRES_DB=style_license_db \
  -e POSTGRES_USER=stylelicense_user \
  -e POSTGRES_PASSWORD=your_password \
  -v /var/lib/postgresql/data:/var/lib/postgresql/data \
  -p 5432:5432 \
  postgres:15

# 백업 디렉토리 생성
sudo mkdir -p /var/backups/postgresql
```

**로컬 설치 (대안)**:
```bash
# PostgreSQL 15 설치
sudo apt update
sudo apt install postgresql-15 postgresql-contrib

# 데이터베이스 생성
sudo -u postgres createdb style_license_db
sudo -u postgres createuser stylelicense_user
sudo -u postgres psql

# PostgreSQL 프롬프트에서
ALTER USER stylelicense_user WITH PASSWORD 'your_password';
GRANT ALL PRIVILEGES ON DATABASE style_license_db TO stylelicense_user;
\q
```

### 2. RabbitMQ 설정

```bash
# Docker로 RabbitMQ 실행
docker run -d \
  --name rabbitmq \
  --restart always \
  -p 5672:5672 \
  -p 15672:15672 \
  -e RABBITMQ_DEFAULT_USER=stylelicense \
  -e RABBITMQ_DEFAULT_PASS=<strong_password> \
  rabbitmq:3-management

# Management UI 접근 (SSH 터널)
ssh -L 15672:localhost:15672 ubuntu@<ec2-ip>
# 브라우저에서 http://localhost:15672 접속
```

### 3. Nginx 설정

**설정 파일**: `/etc/nginx/sites-available/stylelicense`
```nginx
server {
    listen 80;
    server_name stylelicense.com www.stylelicense.com;

    # HTTP를 HTTPS로 리다이렉트
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name stylelicense.com www.stylelicense.com;

    # Let's Encrypt SSL 인증서
    ssl_certificate /etc/letsencrypt/live/stylelicense.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/stylelicense.com/privkey.pem;

    # Frontend 정적 파일
    location / {
        root /var/www/stylelicense/frontend;
        try_files $uri $uri/ /index.html;
    }

    # Backend API (Gunicorn Reverse Proxy)
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # Django Admin
    location /admin/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }

    # Django Static Files (collectstatic)
    location /static/ {
        alias /home/ubuntu/stylelicense/apps/backend/staticfiles/;
    }
}
```

**Let's Encrypt SSL 설치**:
```bash
# Certbot 설치
sudo apt install certbot python3-certbot-nginx

# SSL 인증서 발급
sudo certbot --nginx -d stylelicense.com -d www.stylelicense.com

# 자동 갱신 확인
sudo certbot renew --dry-run
```

**Nginx 활성화**:
```bash
# 설정 파일 심볼릭 링크
sudo ln -s /etc/nginx/sites-available/stylelicense /etc/nginx/sites-enabled/

# 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl restart nginx
```

### 4. Gunicorn 설정

**Systemd 서비스 파일**: `/etc/systemd/system/gunicorn.service`

```ini
[Unit]
Description=Gunicorn daemon for Style License Backend
After=network.target

[Service]
User=ubuntu
Group=www-data
WorkingDirectory=/home/ubuntu/StyleLicense/apps/deploy/backend
ExecStart=/home/ubuntu/StyleLicense/apps/deploy/backend/venv/bin/gunicorn \
          --workers 4 \
          --bind 127.0.0.1:8000 \
          --timeout 120 \
          config.wsgi:application

[Install]
WantedBy=multi-user.target
```

**Gunicorn 서비스 시작**:
```bash
# 서비스 파일 리로드
sudo systemctl daemon-reload

# Gunicorn 시작 및 자동 시작 설정
sudo systemctl start gunicorn
sudo systemctl enable gunicorn

# 상태 확인
sudo systemctl status gunicorn

# 재시작
sudo systemctl restart gunicorn
```

### 5. Database Migration

```bash
# EC2에서 실행
cd /home/ubuntu/StyleLicense/apps/deploy/backend
source venv/bin/activate
python manage.py migrate

# Static 파일 수집
python manage.py collectstatic --noinput
```

### 6. AI Servers Deployment (RunPod GPU Pods)

```bash
# RunPod 웹 콘솔 또는 API를 통해 배포
# 1. Docker 이미지를 Docker Hub 또는 ECR에 Push
docker tag stylelicense-training:latest <registry>/stylelicense-training:latest
docker push <registry>/stylelicense-training:latest

# 2. RunPod 콘솔에서 GPU Pod 생성
# - Template: Custom Docker Image
# - Image: <registry>/stylelicense-training:latest
# - GPU: RTX 4090 (24GB VRAM)
# - 환경변수 설정:
#   - RABBITMQ_HOST=<Backend-Public-IP>
#   - BACKEND_API_URL=https://stylelicense.com
#   - INTERNAL_API_TOKEN=<token>
#   - AWS_ACCESS_KEY_ID=<key>
#   - AWS_SECRET_ACCESS_KEY=<secret>

# 3. Pod 재시작 또는 업데이트
# RunPod 콘솔에서 "Restart Pod" 또는 "Update Template"
```

**무중단 배포**: RabbitMQ 큐에 작업이 남아있으면 순차적으로 처리됨

**RunPod 배포 팁**:
- Pod 템플릿을 저장하여 재사용
- GPU Pod의 Public IP는 고정되지 않을 수 있으므로 Webhook URL을 도메인으로 설정
- RabbitMQ 연결을 위해 Backend EC2의 RabbitMQ 포트(5672)를 Public으로 노출하거나 VPN 사용

---

## Health Checks & Monitoring

### Health Check Endpoints

#### Backend
```bash
# 서버 상태 확인
curl http://backend:8000/api/health

# 예상 응답
{
  "status": "healthy",
  "database": "connected",
  "rabbitmq": "connected"
}
```

#### RabbitMQ
```bash
# 큐 상태 확인 (Management API)
curl -u guest:guest http://rabbitmq:15672/api/queues

# 메시지 수 확인
curl -u guest:guest http://rabbitmq:15672/api/queues/%2F/model_training
```

#### AI Servers (GPU)
```bash
# GPU 사용률 확인
nvidia-smi

# Consumer 프로세스 확인
ps aux | grep python
```

### CloudWatch Logs

프로덕션 환경에서는 CloudWatch로 로그를 수집합니다.

```bash
# Backend 로그 확인
aws logs tail /stylelicense/backend --follow

# Training Server 로그 확인
aws logs tail /stylelicense/training-server --follow
```

### Monitoring Metrics

| 지표 | 도구 | 설명 |
|------|------|------|
| API 응답 시간 | CloudWatch | ALB 메트릭 |
| Database 연결 | RDS Monitoring | Connection count |
| RabbitMQ 큐 길이 | RabbitMQ Management | Queue depth |
| GPU 활용률 | CloudWatch Agent | GPU utilization % |
| 에러 로그 | CloudWatch Logs | 5xx 에러 추적 |

---

## Deployment Strategy

### Blue-Green Deployment (Backend, 향후)

```
Blue (현재 운영 중)
  ↓
Green (새 버전 배포)
  ↓
Health Check 통과
  ↓
ALB 트래픽을 Green으로 전환
  ↓
Blue 종료 (30분 후)
```

**장점**: 무중단 배포, 즉시 롤백 가능

### Rolling Update (AI Servers)

```
Training Server 1대씩 순차 업데이트
  ↓
RabbitMQ에 작업이 있으면 대기
  ↓
작업 완료 후 서버 중지
  ↓
새 버전 시작
  ↓
다음 서버 반복
```

**장점**: GPU 리소스를 최대한 활용하며 안전하게 배포

---

## Troubleshooting

### Common Issues

**1. Docker Compose 실행 실패**
```bash
# 포트 충돌 확인
lsof -i :8000

# 컨테이너 재시작
docker-compose restart backend
```

**2. RabbitMQ 연결 실패**
```bash
# RabbitMQ 상태 확인
docker-compose logs rabbitmq

# 큐 초기화 (주의: 대기 중인 작업 삭제됨)
docker-compose exec rabbitmq rabbitmqctl purge_queue model_training
```

**3. GPU 서버 Out of Memory**
```bash
# GPU 메모리 확인
nvidia-smi

# 컨테이너 재시작
docker restart training-server
```

**4. EC2 배포 실패**
```bash
# Docker 로그 확인
docker logs backend

# 환경변수 확인
docker exec backend env | grep DATABASE_URL
```

**5. Nginx 설정 문제**
```bash
# Nginx 설정 테스트
sudo nginx -t

# Nginx 재시작
sudo systemctl reload nginx

# Nginx 로그 확인
sudo tail -f /var/log/nginx/error.log
sudo tail -f /var/log/nginx/access.log

# SSL 인증서 갱신 문제
sudo certbot renew --dry-run
```

---

## Rollback Procedures

### Backend Rollback

```bash
# 1. 이전 버전 Docker 이미지로 되돌리기
docker stop backend
docker run -d --name backend <ECR_URL>/stylelicense-backend:previous-tag

# 2. Database 마이그레이션 롤백 (필요 시)
docker exec backend python manage.py migrate app 0001  # 이전 마이그레이션으로
```

### Frontend Rollback

```bash
# 1. Git에서 이전 버전 체크아웃
cd apps/frontend
git checkout <previous-commit-hash>

# 2. 재빌드 및 배포
npm run build
scp -r dist/* ubuntu@ec2-backend:/var/www/stylelicense/frontend/

# 3. Nginx 재시작
ssh ubuntu@ec2-backend 'sudo systemctl reload nginx'
```

### AI Servers Rollback

```bash
# RunPod 콘솔에서 이전 Template으로 롤백
# 1. Pod 중지
# 2. Template 변경 (이전 Docker 이미지 태그)
# 3. Pod 재시작

# 또는 CLI를 통한 업데이트
runpodctl update pod <pod-id> --template <previous-template-id>
```

---

## Security Checklist

### Production Deployment

- [ ] 환경변수를 Parameter Store에 암호화 저장
- [ ] Security Group 최소 권한 원칙 적용
- [ ] PostgreSQL 로컬 백업 스크립트 설정 (pg_dump 일일 자동 백업)
- [ ] S3 버킷 퍼블릭 액세스 설정 (생성 이미지는 Public, 학습 이미지는 Private)
- [ ] ALB HTTPS 리스너 설정 (ACM 인증서)
- [ ] INTERNAL_API_TOKEN 32자 이상 UUID 사용
- [ ] RabbitMQ 기본 계정 변경
- [ ] CloudWatch 로그 활성화
- [ ] VPC Flow Logs 활성화
- [ ] IAM Role 최소 권한 부여 (EC2, Lambda)

---

## Cost Optimization

### AWS 비용 절감 전략

| 항목 | 최적화 방법 | 예상 절감 |
|------|------------|----------|
| **RunPod Spot Instances** | Spot GPU Pods 사용 (대기 시간 허용 시) | ~50-70% |
| **S3 Lifecycle Policy** | 오래된 이미지 Glacier로 이동 (90일 후) | ~30% |
| **Backend EC2 Stop/Start** | 개발 환경 야간 자동 중지 | ~50% |
| **Nginx Gzip** | 압축 활성화, 정적 파일 캐싱 최적화 | 대역폭 ~20% |
| **RunPod Auto-Pause** | GPU 미사용 시 자동 일시정지 | ~40% |

---

## References

### 프로젝트 문서
- **[TECHSPEC.md](../../TECHSPEC.md)** - 전체 시스템 아키텍처
- **[docs/database/README.md](../../docs/database/README.md)** - DB 스키마
- **[apps/backend/README.md](../backend/README.md)** - Backend 개발 가이드
- **[apps/frontend/README.md](../frontend/README.md)** - Frontend 개발 가이드

### AWS 문서
- **EC2**: https://docs.aws.amazon.com/ec2/
- **RDS**: https://docs.aws.amazon.com/rds/
- **S3**: https://docs.aws.amazon.com/s3/
- **CloudFront**: https://docs.aws.amazon.com/cloudfront/
- **Systems Manager**: https://docs.aws.amazon.com/systems-manager/

### Docker & CI/CD
- **Docker Compose**: https://docs.docker.com/compose/
- **GitHub Actions**: https://docs.github.com/en/actions
- **NVIDIA Docker**: https://github.com/NVIDIA/nvidia-docker

---

## Support

- **DevOps Issues**: Slack #devops 채널
- **Infrastructure**: AWS Support (Business Plan)
- **Documentation**: [TECHSPEC.md](../../TECHSPEC.md)
