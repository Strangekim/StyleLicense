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

- **Frontend**: http://localhost:3000
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

## Production Setup

Production setup is designed for deployment on EC2 with Nginx reverse proxy and SSL certificates.

### 1. Prepare Server

```bash
# Update system
sudo apt-get update && sudo apt-get upgrade -y

# Install Docker and Docker Compose
# (Follow official installation guide)

# Clone repository
git clone <repository-url>
cd StyleLicense
```

### 2. Configure Environment

```bash
# Copy and configure environment
cp .env.example .env

# Edit .env with production values
nano .env

# IMPORTANT: Set strong passwords and tokens
# - SECRET_KEY (generate with: python -c "import secrets; print(secrets.token_urlsafe(50))")
# - POSTGRES_PASSWORD
# - RABBITMQ_PASSWORD
# - INTERNAL_API_TOKEN
```

### 3. Configure Nginx

```bash
# Edit nginx configuration with your domain
nano nginx/conf.d/default.conf

# Replace "yourdomain.com" with your actual domain
```

### 4. Build Frontend

```bash
cd apps/frontend
npm install
npm run build
cd ../..
```

### 5. Start Services

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f
```

### 6. Setup SSL with Let's Encrypt

```bash
# First, ensure DNS points to your server IP

# Get SSL certificate
docker-compose -f docker-compose.prod.yml run --rm certbot certonly \
    --webroot \
    --webroot-path=/var/www/certbot \
    --email admin@yourdomain.com \
    --agree-tos \
    --no-eff-email \
    -d yourdomain.com \
    -d www.yourdomain.com

# Restart nginx
docker-compose -f docker-compose.prod.yml restart nginx
```

### 7. Initialize Database

```bash
# Run migrations
docker-compose -f docker-compose.prod.yml exec backend python manage.py migrate

# Create superuser
docker-compose -f docker-compose.prod.yml exec backend python manage.py createsuperuser

# Collect static files
docker-compose -f docker-compose.prod.yml exec backend python manage.py collectstatic --noinput
```

---

## AI Servers Setup (GPU Required)

AI servers (Training and Inference) run on separate GPU machines (e.g., RunPod).

### Training Server

```bash
# On GPU machine
cd StyleLicense/apps/training-server

# Build image
docker build -t stylelicense-training .

# Run with GPU
docker run -d \
    --name training-server \
    --gpus all \
    --restart unless-stopped \
    -e RABBITMQ_HOST=<backend-server-ip> \
    -e RABBITMQ_PORT=5672 \
    -e RABBITMQ_USER=admin \
    -e RABBITMQ_PASSWORD=<rabbitmq-password> \
    -e RABBITMQ_QUEUE=model_training \
    -e AWS_ACCESS_KEY_ID=<aws-key> \
    -e AWS_SECRET_ACCESS_KEY=<aws-secret> \
    -e AWS_STORAGE_BUCKET_NAME=<bucket-name> \
    -e AWS_S3_REGION_NAME=us-east-1 \
    -e INTERNAL_API_TOKEN=<internal-token> \
    -e WEBHOOK_BASE_URL=https://yourdomain.com \
    stylelicense-training

# View logs
docker logs -f training-server
```

### Inference Server

```bash
# On GPU machine
cd StyleLicense/apps/inference-server

# Build image
docker build -t stylelicense-inference .

# Run with GPU
docker run -d \
    --name inference-server \
    --gpus all \
    --restart unless-stopped \
    -e RABBITMQ_HOST=<backend-server-ip> \
    -e RABBITMQ_PORT=5672 \
    -e RABBITMQ_USER=admin \
    -e RABBITMQ_PASSWORD=<rabbitmq-password> \
    -e RABBITMQ_QUEUE=image_generation \
    -e AWS_ACCESS_KEY_ID=<aws-key> \
    -e AWS_SECRET_ACCESS_KEY=<aws-secret> \
    -e AWS_STORAGE_BUCKET_NAME=<bucket-name> \
    -e AWS_S3_REGION_NAME=us-east-1 \
    -e INTERNAL_API_TOKEN=<internal-token> \
    -e WEBHOOK_BASE_URL=https://yourdomain.com \
    stylelicense-inference

# View logs
docker logs -f inference-server
```

### Security Configuration

**On Backend Server (EC2):**

1. Allow RabbitMQ connections from AI servers:
```bash
# Edit security group to allow port 5672 from AI server IPs
```

2. Configure firewall (if using ufw):
```bash
sudo ufw allow from <training-server-ip> to any port 5672
sudo ufw allow from <inference-server-ip> to any port 5672
```

**On AI Servers:**

- Ensure `INTERNAL_API_TOKEN` matches the backend
- Use secure RabbitMQ credentials
- Store AWS credentials securely

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
curl http://localhost:3000/health

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
