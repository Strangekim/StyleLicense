# Deploy Configuration

## Overview

Style License 프로젝트의 배포 구성 및 인프라 관리 저장소입니다. Docker Compose를 통한 로컬 개발 환경과 AWS 기반 프로덕션 배포 설정을 포함합니다.

**핵심 역할:**
- Docker Compose로 전체 스택 로컬 실행
- GitHub Actions CI/CD 워크플로우
- AWS 인프라 구성 문서
- 환경변수 관리 템플릿

> **참고**: 이 폴더는 코드가 아닌 **배포 설정**을 관리합니다. 각 앱의 개발 방법은 해당 앱의 README를 참조하세요.

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
  ↓
CloudFront (CDN) → S3 (Frontend 정적 파일)
  ↓
Application Load Balancer
  ↓
EC2 (Backend) ← RabbitMQ (EC2) ← GPU EC2 (Training/Inference)
  ↓
RDS (PostgreSQL)
  ↓
S3 (이미지/모델 파일)
```

### 인스턴스 구성

| 서비스 | 인스턴스 타입 | 수량 | 설명 |
|--------|--------------|------|------|
| **Backend** | EC2 t3.medium | 1~2 | Django + Gunicorn |
| **Frontend** | S3 + CloudFront | - | 정적 호스팅 (CDN) |
| **Database** | RDS db.t3.small | 1 | PostgreSQL 15 |
| **Queue** | EC2 t3.small | 1 | RabbitMQ |
| **Training Server** | EC2 g4dn.xlarge | 1 | GPU (NVIDIA T4) |
| **Inference Server** | EC2 g4dn.xlarge | 1~2 | GPU (NVIDIA T4) |
| **Storage** | S3 | - | 이미지/모델 저장 |

### 네트워크 구성

- **VPC**: Private Subnet (Backend, RDS, RabbitMQ, GPU)
- **Public Subnet**: ALB (Application Load Balancer)
- **Security Groups**:
  - ALB: 80, 443 포트 허용 (Public)
  - Backend: 8000 포트 (ALB에서만)
  - RabbitMQ: 5672 포트 (Backend, GPU 서버만)
  - RDS: 5432 포트 (Backend만)
  - GPU Servers: Webhook 송신용 (Backend API로만)

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

## CI/CD Pipeline

### GitHub Actions Workflow

각 앱마다 독립적인 CI/CD 파이프라인이 실행됩니다.

#### Backend Pipeline

```
트리거: push to main (apps/backend/** 변경 시)
  ↓
1. Lint (Black, Pylint)
  ↓
2. Test (pytest)
  ↓
3. Build Docker Image
  ↓
4. Push to ECR (AWS Container Registry)
  ↓
5. Deploy to EC2 (SSH + Docker)
  ↓
6. Health Check (GET /api/health)
```

**파일**: `.github/workflows/backend.yml`

#### Frontend Pipeline

```
트리거: push to main (apps/frontend/** 변경 시)
  ↓
1. Lint (ESLint)
  ↓
2. Test (Vitest, E2E Playwright)
  ↓
3. Build (Vite)
  ↓
4. Deploy to S3
  ↓
5. Invalidate CloudFront Cache
```

**파일**: `.github/workflows/frontend.yml`

#### AI Servers Pipeline

```
트리거: push to main (apps/training-server/** 또는 apps/inference-server/** 변경 시)
  ↓
1. Lint (Black, Pylint)
  ↓
2. Test (pytest)
  ↓
3. Build Docker Image
  ↓
4. Push to ECR
  ↓
5. Deploy to GPU EC2 (Rolling Update)
  ↓
6. Health Check (RabbitMQ Consumer 확인)
```

**파일**: `.github/workflows/training-server.yml`, `.github/workflows/inference-server.yml`

---

## Deployment Guide

### 1. Backend Deployment (EC2)

```bash
# EC2 인스턴스 접속
ssh -i keypair.pem ubuntu@ec2-backend.ap-northeast-2.compute.amazonaws.com

# Docker 이미지 Pull
aws ecr get-login-password --region ap-northeast-2 | docker login --username AWS --password-stdin <ECR_URL>
docker pull <ECR_URL>/stylelicense-backend:latest

# 기존 컨테이너 중지
docker stop backend

# 새 컨테이너 실행
docker run -d \
  --name backend \
  -p 8000:8000 \
  -e DATABASE_URL=$(aws ssm get-parameter --name /stylelicense/prod/DATABASE_URL --with-decryption --query Parameter.Value --output text) \
  -e SECRET_KEY=$(aws ssm get-parameter --name /stylelicense/prod/SECRET_KEY --with-decryption --query Parameter.Value --output text) \
  <ECR_URL>/stylelicense-backend:latest

# Health Check
curl http://localhost:8000/api/health
```

### 2. Frontend Deployment (S3 + CloudFront)

```bash
# 1. 로컬에서 빌드
cd apps/frontend
npm run build

# 2. S3 업로드
aws s3 sync dist/ s3://stylelicense-frontend --delete

# 3. CloudFront 캐시 무효화
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"
```

**자동화**: GitHub Actions에서 자동 실행됨

### 3. Database Migration

```bash
# EC2 Backend 컨테이너에서 실행
docker exec -it backend python manage.py migrate

# 또는 SSH로 직접 실행
ssh -i keypair.pem ubuntu@ec2-backend.ap-northeast-2.compute.amazonaws.com
cd /home/ubuntu/stylelicense/apps/backend
python manage.py migrate
```

### 4. AI Servers Deployment (Rolling Update)

```bash
# Training Server 배포 (순차적으로 1대씩)
# 1번 서버 업데이트
ssh gpu-training-1
docker stop training-server
docker pull <ECR_URL>/stylelicense-training:latest
docker run -d --gpus all <ECR_URL>/stylelicense-training:latest

# 2번 서버 업데이트 (1번 완료 후)
ssh gpu-training-2
...
```

**무중단 배포**: RabbitMQ 큐에 작업이 남아있으면 순차적으로 처리됨

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

**5. CloudFront 캐시 문제**
```bash
# 캐시 무효화
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/*"

# 특정 파일만 무효화
aws cloudfront create-invalidation \
  --distribution-id E1234567890ABC \
  --paths "/index.html" "/assets/*"
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
# 1. S3에서 이전 버전 복원
aws s3 sync s3://stylelicense-frontend-backup/previous-version/ s3://stylelicense-frontend/ --delete

# 2. CloudFront 캐시 무효화
aws cloudfront create-invalidation --distribution-id E1234567890ABC --paths "/*"
```

### AI Servers Rollback

```bash
# GPU 서버에서 이전 Docker 이미지로 롤백
docker stop training-server
docker run -d --gpus all <ECR_URL>/stylelicense-training:previous-tag
```

---

## Security Checklist

### Production Deployment

- [ ] 환경변수를 Parameter Store에 암호화 저장
- [ ] Security Group 최소 권한 원칙 적용
- [ ] RDS 백업 활성화 (자동 백업 7일 보관)
- [ ] S3 버킷 퍼블릭 액세스 차단 (CloudFront만 허용)
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
| **EC2 Reserved Instance** | Training/Inference 서버 RI 구매 (1년) | ~40% |
| **S3 Lifecycle Policy** | 오래된 이미지 Glacier로 이동 (90일 후) | ~30% |
| **RDS Stop/Start** | 개발 환경 야간 자동 중지 | ~50% |
| **CloudFront** | 압축 활성화, 캐시 TTL 최적화 | ~20% |
| **Spot Instances** | Training Server에 Spot 사용 (비상용) | ~70% |

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
