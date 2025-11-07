# Docker Setup Guide

This document provides instructions for running Style License using Docker containers.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Development Setup](#development-setup)
3. [Production Setup](#production-setup)
4. [AI Servers Setup (GPU Required)](#ai-servers-setup-gpu-required)
5. [Common Commands](#common-commands)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

### For All Environments

- **Docker**: Version 20.10 or later
- **Docker Compose**: Version 2.0 or later

Install Docker:
- **macOS/Windows**: [Docker Desktop](https://www.docker.com/products/docker-desktop)
- **Linux**: Follow [official Docker installation guide](https://docs.docker.com/engine/install/)

### For AI Servers (Training/Inference)

- **NVIDIA GPU**: CUDA-compatible GPU (GTX 1060 or better)
- **NVIDIA Driver**: Version 525.60.13 or later
- **NVIDIA Container Toolkit**: For Docker GPU support

Install NVIDIA Container Toolkit (Linux):
```bash
distribution=$(. /etc/os-release;echo $ID$VERSION_ID)
curl -s -L https://nvidia.github.io/libnvidia-container/gpgkey | sudo apt-key add -
curl -s -L https://nvidia.github.io/libnvidia-container/$distribution/libnvidia-container.list | \
    sudo tee /etc/apt/sources.list.d/nvidia-container-toolkit.list

sudo apt-get update
sudo apt-get install -y nvidia-container-toolkit
sudo systemctl restart docker
```

---

## Development Setup

Development setup runs Backend, Frontend, PostgreSQL, and RabbitMQ locally. AI servers are typically run on separate GPU machines.

### 1. Clone Repository

```bash
git clone <repository-url>
cd StyleLicense
```

### 2. Configure Environment

```bash
# Copy example environment file
cp .env.example .env

# Edit .env and fill in required values
# At minimum, set:
# - AWS credentials (for S3)
# - Google OAuth credentials
# - INTERNAL_API_TOKEN
```

### 3. Start Services

```bash
# Start all services
docker-compose up -d

# View logs
docker-compose logs -f

# Check status
docker-compose ps
```

### 4. Initialize Database

```bash
# Run migrations
docker-compose exec backend python manage.py migrate

# Create superuser (optional)
docker-compose exec backend python manage.py createsuperuser

# Collect static files
docker-compose exec backend python manage.py collectstatic --noinput
```

### 5. Access Services

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000/api
- **Django Admin**: http://localhost:8000/admin
- **RabbitMQ Management**: http://localhost:15672 (guest/guest)
- **PostgreSQL**: localhost:5432

### 6. Stop Services

```bash
# Stop all services
docker-compose down

# Stop and remove volumes (CAUTION: deletes all data)
docker-compose down -v
```

---

## Production Setup (GCP)

**주의**: 프로덕션 환경은 더 이상 `docker-compose.prod.yml`을 사용하지 않습니다. 각 서비스는 역할에 맞는 최적의 GCP 서비스에 개별적으로 배포됩니다.

배포에 대한 자세한 내용은 각 서비스의 `README.md`를 참고하세요.

- **Backend**: `apps/backend/README.md` → **Google Cloud Run**에 배포
- **Frontend**: `apps/frontend/README.md` → **Google Cloud Storage**에 배포
- **Database**: `docs/database/README.md` → **Google Cloud SQL**에서 호스팅
- **AI Servers**: `apps/training-server/README.md` → **Google Compute Engine (GCE)**에 배포

---

## AI Servers Setup (GCP - GCE)

AI 서버 (Training/Inference)는 GPU가 연결된 별도의 Google Compute Engine(GCE) VM에서 Docker 컨테이너로 실행됩니다.

### 1. GCE VM 생성

- GCP 콘솔 또는 `gcloud` CLI를 사용하여 GPU가 장착된 VM을 생성합니다. (자세한 내용은 각 AI 서버의 `README.md` 참고)
- **중요**: VM 생성 시, Cloud Storage 등 다른 GCP 서비스에 접근할 수 있는 권한을 가진 **서비스 계정(Service Account)**을 연결합니다. 이를 통해 별도의 인증 키 없이 안전하게 서비스 이용이 가능합니다.

### 2. Docker 컨테이너 실행

VM에 SSH로 접속한 후, 각 서버의 Docker 이미지를 빌드하고 실행합니다.

#### Training Server
```bash
# On GCE VM for Training
cd StyleLicense/apps/training-server

# Build image
docker build -t stylelicense-training .

# Run with GPU
docker run -d \
    --name training-server \
    --gpus all \
    --restart unless-stopped \
    -e RABBITMQ_HOST=<rabbitmq-vm-internal-ip> \
    -e GCS_BUCKET_NAME=<your-gcs-bucket-name> \
    -e INTERNAL_API_TOKEN=<internal-token> \
    -e BACKEND_API_URL=https://your-backend-domain.com \
    stylelicense-training
```

#### Inference Server
```bash
# On GCE VM for Inference
cd StyleLicense/apps/inference-server

# Build image
docker build -t stylelicense-inference .

# Run with GPU
docker run -d \
    --name inference-server \
    --gpus all \
    --restart unless-stopped \
    -e RABBITMQ_HOST=<rabbitmq-vm-internal-ip> \
    -e GCS_BUCKET_NAME=<your-gcs-bucket-name> \
    -e INTERNAL_API_TOKEN=<internal-token> \
    -e BACKEND_API_URL=https://your-backend-domain.com \
    stylelicense-inference
```

### 3. 방화벽 설정

- **RabbitMQ VM**: AI 서버 VM들의 내부 IP로부터 오는 5672 포트 트래픽을 허용하도록 방화벽 규칙을 설정합니다.
- **Backend (Cloud Run)**: 기본적으로 Public URL로 접근 가능하며, `INTERNAL_API_TOKEN`으로 내부 요청을 인증합니다.

---

## RabbitMQ Setup (GCP - GCE)

RabbitMQ는 메시지 큐 시스템으로, Backend와 AI 서버 간 비동기 작업 분배에 사용됩니다. Google Compute Engine (GCE) VM에서 Docker 컨테이너로 실행됩니다.

### 1. GCE VM 생성

```bash
# GCP 프로젝트 ID 설정
export PROJECT_ID=your-gcp-project-id
export REGION=asia-northeast3
export ZONE=asia-northeast3-a

# RabbitMQ VM 생성
gcloud compute instances create stylelicense-rabbitmq \
    --project=$PROJECT_ID \
    --zone=$ZONE \
    --machine-type=e2-medium \
    --boot-disk-size=20GB \
    --boot-disk-type=pd-standard \
    --image-family=debian-11 \
    --image-project=debian-cloud \
    --tags=rabbitmq-server \
    --metadata=startup-script='#!/bin/bash
# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sh get-docker.sh
usermod -aG docker $USER

# Run RabbitMQ container
docker run -d \
    --name rabbitmq \
    --restart unless-stopped \
    -e RABBITMQ_DEFAULT_USER=admin \
    -e RABBITMQ_DEFAULT_PASS=CHANGE_THIS_PASSWORD \
    -v rabbitmq_data:/var/lib/rabbitmq \
    -p 5672:5672 \
    -p 15672:15672 \
    rabbitmq:3-management-alpine
'
```

### 2. 방화벽 규칙 생성

#### 내부 트래픽 허용 (AMQP 포트)

Backend (Cloud Run)와 AI 서버 (GCE)가 RabbitMQ에 접근할 수 있도록 내부 트래픽을 허용합니다.

```bash
# AI Servers와 Backend로부터 오는 5672 포트 허용
gcloud compute firewall-rules create allow-rabbitmq-internal \
    --project=$PROJECT_ID \
    --direction=INGRESS \
    --priority=1000 \
    --network=default \
    --action=ALLOW \
    --rules=tcp:5672 \
    --source-ranges=10.0.0.0/8 \
    --target-tags=rabbitmq-server \
    --description="Allow internal access to RabbitMQ AMQP port"
```

#### 관리 UI 접근 (선택사항)

⚠️ **주의**: 프로덕션 환경에서는 관리 UI를 공개하지 않는 것이 안전합니다. 필요 시 Cloud IAP (Identity-Aware Proxy) 또는 SSH 터널링을 사용하세요.

```bash
# SSH 터널링으로 관리 UI 접근 (권장)
gcloud compute ssh stylelicense-rabbitmq \
    --zone=$ZONE \
    --ssh-flag="-L 15672:localhost:15672"

# 브라우저에서 http://localhost:15672 접근
# ID: admin, PW: (VM 생성 시 설정한 비밀번호)
```

### 3. Cloud Run에서 RabbitMQ 접근 설정

Cloud Run은 기본적으로 외부 네트워크만 접근 가능하므로, **Serverless VPC Access Connector**를 생성하여 내부 네트워크 접근이 가능하도록 합니다.

```bash
# VPC Connector 생성 (최초 1회만)
gcloud compute networks vpc-access connectors create stylelicense-connector \
    --region=$REGION \
    --subnet-project=$PROJECT_ID \
    --subnet=default \
    --min-instances=2 \
    --max-instances=10

# Backend Cloud Run에 VPC Connector 연결
gcloud run services update backend \
    --vpc-connector stylelicense-connector \
    --vpc-egress all-traffic \
    --region=$REGION
```

이제 Backend (Cloud Run)는 RabbitMQ VM의 **내부 IP**로 접근할 수 있습니다:
```bash
# RabbitMQ VM의 내부 IP 확인
gcloud compute instances describe stylelicense-rabbitmq \
    --zone=$ZONE \
    --format='get(networkInterfaces[0].networkIP)'

# 출력 예: 10.128.0.5
# Backend 환경 변수에 설정: RABBITMQ_HOST=10.128.0.5
```

### 4. RabbitMQ 모니터링 및 관리

#### 컨테이너 상태 확인

```bash
# VM에 SSH 접속
gcloud compute ssh stylelicense-rabbitmq --zone=$ZONE

# RabbitMQ 컨테이너 상태 확인
docker ps | grep rabbitmq

# RabbitMQ 로그 확인
docker logs rabbitmq

# RabbitMQ 재시작
docker restart rabbitmq
```

#### Health Check

```bash
# RabbitMQ 진단 명령어
docker exec rabbitmq rabbitmq-diagnostics ping

# 큐 목록 확인
docker exec rabbitmq rabbitmqctl list_queues

# 연결 목록 확인
docker exec rabbitmq rabbitmqctl list_connections
```

### 5. 백업 및 복구

RabbitMQ 데이터는 Docker 볼륨 (`rabbitmq_data`)에 저장됩니다.

```bash
# VM 스냅샷 생성 (백업)
gcloud compute disks snapshot stylelicense-rabbitmq \
    --zone=$ZONE \
    --snapshot-names=rabbitmq-backup-$(date +%Y%m%d)

# 볼륨 백업 (VM 내부에서)
docker run --rm \
    -v rabbitmq_data:/data \
    -v $(pwd):/backup \
    alpine tar czf /backup/rabbitmq-data-backup.tar.gz /data
```

### 6. 대안: Cloud Pub/Sub 마이그레이션 계획

**장기적 권장사항**: RabbitMQ on GCE 대신 **Cloud Pub/Sub**로 마이그레이션하면 다음 장점이 있습니다:

- ✅ **서버리스**: VM 관리 불필요
- ✅ **고가용성**: 99.95% SLA, 자동 복제
- ✅ **자동 확장**: 트래픽에 따라 자동 확장
- ✅ **비용 효율적**: 사용량 기반 과금 (메시지당 $0.40/백만)

**마이그레이션 작업**:
- Backend: `pika` → `google-cloud-pubsub`
- AI Servers: `pika` → `google-cloud-pubsub`
- 메시지 포맷 변경: RabbitMQ → Pub/Sub 형식

현재는 기존 코드 재사용을 위해 RabbitMQ를 사용하지만, 향후 Pub/Sub로 전환하면 운영 부담이 크게 줄어듭니다.

---

## Common Commands

### Development

```bash
# Start services
docker-compose up -d

# Stop services
docker-compose down

# Restart a service
docker-compose restart backend

# View logs
docker-compose logs -f backend

# Execute command in container
docker-compose exec backend python manage.py shell

# Rebuild images
docker-compose build

# Pull latest images
docker-compose pull
```

### Production

```bash
# Start services
docker-compose -f docker-compose.prod.yml up -d

# View logs
docker-compose -f docker-compose.prod.yml logs -f

# Restart services
docker-compose -f docker-compose.prod.yml restart

# Database backup
docker-compose -f docker-compose.prod.yml exec postgres pg_dump -U postgres stylelicense_db > backup.sql

# Database restore
docker-compose -f docker-compose.prod.yml exec -T postgres psql -U postgres stylelicense_db < backup.sql
```

### Monitoring

```bash
# Resource usage
docker stats

# Container health
docker ps --format "table {{.Names}}\t{{.Status}}\t{{.Ports}}"

# Disk usage
docker system df

# Clean up
docker system prune -a
```

---

## Troubleshooting

### Common Issues

**1. Backend won't start**

```bash
# Check logs
docker-compose logs backend

# Common causes:
# - Database not ready: Wait for postgres healthcheck
# - Missing environment variables: Check .env file
# - Port already in use: Change port in docker-compose.yml
```

**2. Database connection failed**

```bash
# Check postgres is running
docker-compose ps postgres

# Check database credentials
docker-compose exec postgres psql -U postgres -d stylelicense_db

# Reset database (CAUTION: deletes all data)
docker-compose down -v
docker-compose up -d postgres
docker-compose exec backend python manage.py migrate
```

**3. RabbitMQ connection refused**

```bash
# Check RabbitMQ is running
docker-compose ps rabbitmq

# Check RabbitMQ logs
docker-compose logs rabbitmq

# Access management UI
# http://localhost:15672 (guest/guest)
```

**4. GPU not detected in AI servers**

```bash
# Check NVIDIA driver
nvidia-smi

# Check Docker can access GPU
docker run --rm --gpus all nvidia/cuda:12.1.0-base-ubuntu22.04 nvidia-smi

# Check container GPU access
docker exec -it training-server nvidia-smi
```

**5. SSL certificate issues**

```bash
# Check certificate validity
docker-compose -f docker-compose.prod.yml exec nginx \
    openssl x509 -in /etc/letsencrypt/live/yourdomain.com/fullchain.pem -text -noout

# Renew certificate manually
docker-compose -f docker-compose.prod.yml run --rm certbot renew

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### Health Checks

```bash
# Backend health
curl http://localhost:8000/api/health

# Frontend health
curl http://localhost:5173/health

# RabbitMQ health
curl http://localhost:15672/api/healthchecks/node

# Database health
docker-compose exec postgres pg_isready -U postgres
```

### Logs Location

- **Development**: Console output via `docker-compose logs`
- **Production**:
  - Container logs: `/var/lib/docker/containers/<container-id>/`
  - Nginx logs: `./nginx/logs/`
  - Application logs: Inside containers at `/app/logs/`

---

## Additional Resources

- **Project Documentation**: [TECHSPEC.md](TECHSPEC.md)
- **API Documentation**: [docs/API.md](docs/API.md)
- **Database Schema**: [docs/database/README.md](docs/database/README.md)
- **Backend Guide**: [apps/backend/README.md](apps/backend/README.md)
- **Frontend Guide**: [apps/frontend/README.md](apps/frontend/README.md)

---

## Support

For issues or questions:
- Check logs: `docker-compose logs -f`
- Review documentation
- Check GitHub Issues
- Contact team via Slack
