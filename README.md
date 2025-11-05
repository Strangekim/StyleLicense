<div align="center">

<img src="apps/frontend/src/assets/images/main_logo.png" alt="Style License Logo" width="400"/>

# Style License

**AI-Powered Art Style Licensing & Creative Platform**

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![Python](https://img.shields.io/badge/python-3.11-blue.svg)](https://www.python.org/)
[![Vue](https://img.shields.io/badge/vue-3.3+-green.svg)](https://vuejs.org/)
[![Django](https://img.shields.io/badge/django-4.2-darkgreen.svg)](https://www.djangoproject.com/)
[![PostgreSQL](https://img.shields.io/badge/postgresql-15-blue.svg)](https://www.postgresql.org/)

[Features](#-key-features) • [Tech Stack](#-tech-stack) • [Getting Started](#-getting-started) • [Documentation](#-documentation) • [Architecture](#-architecture)

</div>

---

## 📖 Overview

**Style License** is a revolutionary platform that enables digital artists to monetize their unique art styles through AI-powered licensing. Artists can train custom AI models on their artwork, and users can generate new images in licensed styles with guaranteed copyright protection.

### 🎯 Core Value Proposition

- **🎨 Protect Artist Rights**: Clear copyright protection for artistic styles
- **🤝 Transparent Licensing**: Legal and ethical AI art style monetization
- **✨ Commercial Use**: Generate and commercially use AI-created artwork with licensed styles
- **🔒 Copyright Guaranteed**: Automatic artist signature embedding in all generated images

---

## ✨ Key Features

### For Artists

- **🖼️ Style Model Creation**: Upload 10-100 training images to create AI models
- **💰 Flexible Pricing**: Set custom token pricing per generated image
- **📊 Training Progress**: Real-time LoRA fine-tuning progress tracking
- **✍️ Signature Protection**: Automatic watermark insertion on all generated images
- **💵 Revenue Sharing**: Earn tokens from every image generation

### For Users

- **🎭 Browse Style Gallery**: Discover unique art styles from various artists
- **⚡ Instant Generation**: Generate images in licensed styles within seconds
- **🎛️ Customizable Options**: Multiple aspect ratios (1:1, 16:9, 9:16, 4:3, 3:4)
- **🔖 Tag-Based Prompts**: English keyword-based prompt system
- **📱 Community Feed**: Share and discover generated artwork

### Platform Features

- **🪙 Token Economy**: Secure token-based payment system
- **🔐 Google OAuth**: Simple authentication with Google accounts
- **🔔 Notifications**: Real-time updates for training, generation, and social interactions
- **💬 Social Features**: Like, comment, and follow other creators
- **🔍 Advanced Search**: Find styles by tags, artists, or popularity

---

## 🛠️ Tech Stack

### Frontend
![Vue.js](https://img.shields.io/badge/Vue.js-3.3+-4FC08D?logo=vue.js&logoColor=white)
![Vite](https://img.shields.io/badge/Vite-5.0+-646CFF?logo=vite&logoColor=white)
![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4+-06B6D4?logo=tailwindcss&logoColor=white)
![Pinia](https://img.shields.io/badge/Pinia-2.1+-yellow?logo=pinia&logoColor=white)
![Axios](https://img.shields.io/badge/Axios-1.6+-5A29E4?logo=axios&logoColor=white)

### Backend
![Django](https://img.shields.io/badge/Django-4.2-092E20?logo=django&logoColor=white)
![DRF](https://img.shields.io/badge/Django_REST-3.14+-A30000?logo=django&logoColor=white)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-4169E1?logo=postgresql&logoColor=white)
![RabbitMQ](https://img.shields.io/badge/RabbitMQ-3.12-FF6600?logo=rabbitmq&logoColor=white)
![Gunicorn](https://img.shields.io/badge/Gunicorn-21.2-499848?logo=gunicorn&logoColor=white)

### AI/ML
![PyTorch](https://img.shields.io/badge/PyTorch-2.1+-EE4C2C?logo=pytorch&logoColor=white)
![Stable Diffusion](https://img.shields.io/badge/Stable_Diffusion-v1.5-purple)
![LoRA](https://img.shields.io/badge/LoRA-Fine--tuning-orange)
![Diffusers](https://img.shields.io/badge/🤗_Diffusers-0.24+-yellow)
![CUDA](https://img.shields.io/badge/CUDA-12.1-76B900?logo=nvidia&logoColor=white)

### Infrastructure
![Docker](https://img.shields.io/badge/Docker-24.0+-2496ED?logo=docker&logoColor=white)
![Nginx](https://img.shields.io/badge/Nginx-1.24-009639?logo=nginx&logoColor=white)
![AWS S3](https://img.shields.io/badge/AWS_S3-Storage-FF9900?logo=amazons3&logoColor=white)

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         Client (Browser)                        │
│                    Vue 3 + Tailwind CSS                         │
└────────────────┬────────────────────────────────────────────────┘
                 │ HTTPS / Session Cookie
                 ▼
┌─────────────────────────────────────────────────────────────────┐
│                      Backend API Server                         │
│              Django REST Framework + PostgreSQL                 │
└─────┬──────────────────────────────────────────────┬────────────┘
      │                                              │
      │ RabbitMQ                                     │ RabbitMQ
      │ (model_training)                             │ (image_generation)
      ▼                                              ▼
┌──────────────────────┐                  ┌──────────────────────┐
│  Training Server     │                  │  Inference Server    │
│  LoRA Fine-tuning    │                  │  Image Generation    │
│  PyTorch + PEFT      │                  │  Stable Diffusion    │
│  CUDA RTX 4090       │                  │  + LoRA Weights      │
└──────────────────────┘                  └──────────────────────┘
         │                                           │
         └─────────────┬─────────────────────────────┘
                       ▼
              ┌─────────────────┐
              │   AWS S3        │
              │  Model Storage  │
              │  Image Storage  │
              └─────────────────┘
```

### Component Overview

| Component | Technology | Purpose |
|-----------|-----------|---------|
| **Frontend** | Vue 3 + Vite | SPA with Instagram-inspired UI |
| **Backend** | Django + DRF | REST API, authentication, business logic |
| **Database** | PostgreSQL 15 | User data, models, transactions |
| **Message Queue** | RabbitMQ | Async task distribution |
| **Training Server** | PyTorch + LoRA | Fine-tune Stable Diffusion models |
| **Inference Server** | Diffusers | Generate images with trained models |
| **Storage** | AWS S3 | Store models, images, signatures |
| **Proxy** | Nginx | Reverse proxy, SSL termination |

---

## 🚀 Getting Started

### Prerequisites

- **Docker** & **Docker Compose** (recommended)
- **Node.js** 18+ and npm (for frontend)
- **Python** 3.11+ (for backend/AI servers)
- **PostgreSQL** 15+ (if running without Docker)
- **CUDA** 12.1+ (for GPU-accelerated training/inference)

### Quick Start with Docker

```bash
# 1. Clone the repository
git clone https://github.com/your-org/stylelicense.git
cd stylelicense

# 2. Set up environment variables
cp .env.example .env
# Edit .env with your configuration

# 3. Start all services
docker-compose up -d

# 4. Initialize database
docker-compose exec backend python manage.py migrate
docker-compose exec backend python manage.py createsuperuser

# 5. Access the application
# Frontend: http://localhost:3000
# Backend API: http://localhost:8000
# RabbitMQ Management: http://localhost:15672
```

### Development Setup

<details>
<summary><b>Frontend Setup</b></summary>

```bash
cd apps/frontend

# Install dependencies
npm install

# Set environment variables
cp .env.example .env

# Start dev server
npm run dev
```

</details>

<details>
<summary><b>Backend Setup</b></summary>

```bash
cd apps/backend

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Start dev server
python manage.py runserver
```

</details>

<details>
<summary><b>AI Servers Setup</b></summary>

```bash
# Training Server
cd apps/training-server
pip install -r requirements.txt
python rabbitmq_consumer.py

# Inference Server
cd apps/inference-server
pip install -r requirements.txt
python rabbitmq_consumer.py
```

</details>

---

## 📂 Project Structure

```
StyleLicense/
├── apps/
│   ├── backend/              # Django REST API
│   ├── frontend/             # Vue 3 SPA
│   ├── training-server/      # LoRA Fine-tuning
│   └── inference-server/     # Image Generation
│
├── docs/
│   ├── design/pages/         # UI Design Mockups (17 screens)
│   ├── database/             # Database Schema
│   ├── API.md                # API Documentation
│   └── PATTERNS.md           # Code Patterns
│
├── docker-compose.yml        # Development Environment
├── docker-compose.prod.yml   # Production Environment
├── TECHSPEC.md               # Technical Specification
├── PLAN.md                   # Development Roadmap
└── README.md                 # This file
```

---

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [TECHSPEC.md](TECHSPEC.md) | Complete technical specification |
| [PLAN.md](PLAN.md) | Development milestones and progress |
| [API.md](docs/API.md) | REST API endpoints and schemas |
| [Database Schema](docs/database/README.md) | PostgreSQL schema and relationships |
| [Frontend Guide](apps/frontend/README.md) | Vue 3 architecture and design system |
| [Backend Guide](apps/backend/README.md) | Django REST Framework patterns |
| [Training Server](apps/training-server/README.md) | LoRA fine-tuning pipeline |
| [Inference Server](apps/inference-server/README.md) | Image generation pipeline |
| [Docker Guide](DOCKER.md) | Deployment and container setup |

---

## 🎨 Screenshots

<details>
<summary><b>View UI Mockups</b></summary>

Our platform features an Instagram-inspired design with 17 carefully crafted screens:

- **Authentication**: Google OAuth login
- **Main Feed**: Public gallery with infinite scroll
- **Style Marketplace**: Browse and search art styles
- **Style Detail**: Sample gallery and generation interface
- **Profile Pages**: Artist portfolios and user profiles
- **Creation Flow**: Multi-step style model creation
- **Notifications**: Real-time updates
- **Community**: Comments, likes, follows

> 📁 View all mockups: [docs/design/pages/](docs/design/pages/)

</details>

---

## 🔒 Security

- **Session-based Authentication**: Secure cookie-based sessions with Google OAuth
- **CSRF Protection**: Django CSRF middleware enabled
- **SQL Injection Prevention**: Django ORM parameterized queries
- **XSS Protection**: Vue 3 automatic escaping + CSP headers
- **HTTPS Only**: SSL/TLS encryption in production
- **Rate Limiting**: Token bucket algorithm for API endpoints
- **Signature Protection**: Immutable watermarks on generated images

---

## 🧪 Testing

```bash
# Frontend tests
cd apps/frontend
npm run test           # Unit tests (Vitest)
npm run test:e2e       # E2E tests (Playwright)

# Backend tests
cd apps/backend
python manage.py test  # Django tests
pytest                 # Unit tests

# Code quality
npm run lint           # Frontend linting
pylint app/            # Backend linting
```

---

## 🤝 Contributing

We welcome contributions! Please follow these steps:

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Read the relevant CODE_GUIDE.md in the app directory
4. Follow the design system guidelines (see [Frontend README](apps/frontend/README.md#design-system))
5. Commit your changes (`git commit -m 'feat: add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

**Development Guidelines**:
- Follow [TECHSPEC.md](TECHSPEC.md) for feature requirements
- Check [PLAN.md](PLAN.md) for current milestones
- Use [CODE_GUIDE.md](apps/*/CODE_GUIDE.md) for code patterns
- Match design mockups in [docs/design/pages/](docs/design/pages/)

---

## 📊 Project Status

**Current Version**: MVP Development (M1 Foundation)

**Progress**:
- ✅ Project setup and architecture design
- ✅ Database schema and models
- ✅ Docker infrastructure
- 🚧 Authentication system (In Progress)
- ⏳ Core backend APIs (Planned)
- ⏳ Frontend UI implementation (Planned)
- ⏳ AI training/inference pipeline (Planned)

See [PLAN.md](PLAN.md) for detailed milestones and task tracking.

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 👥 Team

**SSAFY 12th - Autonomous Project**

- **Project Duration**: 2025-01 ~ 2025-02
- **Team Size**: [Your team size]
- **Organization**: Samsung Software Academy For Youth

---

## 🙏 Acknowledgments

- [Stable Diffusion](https://github.com/CompVis/stable-diffusion) - Base AI model
- [LoRA](https://github.com/microsoft/LoRA) - Parameter-efficient fine-tuning
- [Hugging Face Diffusers](https://github.com/huggingface/diffusers) - Diffusion models library
- Instagram - UI/UX design inspiration

---

<div align="center">

**Built with ❤️ by the Style License Team**

[Report Bug](https://github.com/your-org/stylelicense/issues) • [Request Feature](https://github.com/your-org/stylelicense/issues) • [Documentation](TECHSPEC.md)

</div>
