# StyleLicense
StyleLicense

```
project-root/
├── README.md                         # 프로젝트 소개 (외부용)
├── claude.md                         # Claude 작업 흐름 가이드 (진입점)
├── TECHSPEC.md                       # 전체 시스템 Context (요약본)
├── PLAN.md                          # 전체 Milestone 추적
├── docs/
│   ├── database/
│   │   └── README.md                # DB 스키마 상세
│   ├── API.md                       # API 명세
│   ├── SECURITY.md                  # 보안 정책
│   ├── DEPLOYMENT.md                # 배포 가이드
│   └── PATTERNS.md                  # 공통 코드 패턴
│
├── design/                          # 디자인 리소스 
│   └── README.md                    # 디자인 시스템 개요
└── apps/
    ├── backend/
    │   ├── README.md                # Backend 개요
    │   ├── PLAN.md                  # Backend Task 추적
    │   └── CODE_GUIDE.md            # Backend 코드 가이드
    │
    ├── frontend/
    │   ├── README.md                # Frontend 개요
    │   ├── PLAN.md                  # Frontend Task 추적
    │   └── CODE_GUIDE.md            # Frontend 코드 가이드
    │
    ├── training-server/
    │   ├── README.md                # Training Server 개요
    │   ├── PLAN.md                  # Training Task 추적
    │   └── CODE_GUIDE.md            # Training 코드 가이드
    │
    ├── inference-server/
    │   ├── README.md                # Inference Server 개요
    │   ├── PLAN.md                  # Inference Task 추적
    │   └── CODE_GUIDE.md            # Inference 코드 가이드
    │
    └── deploy/
        ├── README.md                # 배포 가이드
        ├── docker-compose.yml       # 개발 환경
        └── scripts/                 # 배포 스크립트
```