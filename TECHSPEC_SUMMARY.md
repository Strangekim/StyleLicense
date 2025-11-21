# Style License 기술 명세 요약 (TECHSPEC_SUMMARY.md)

이 문서는 Style License 프로젝트의 핵심 기술 명세와 아키텍처를 요약하여 AI 에이전트 및 신규 참여자가 프로젝트의 전체 구조를 빠르게 파악할 수 있도록 돕는 것을 목표로 합니다.

---

## 1. 프로젝트 핵심 정체성

- **프로젝트명**: Style License
- **목적**: AI 기반 화풍 라이선싱 및 2차 창작 플랫폼. 작가가 자신의 화풍(Style)을 등록하면, 사용자는 라이선스를 구매하여 해당 화풍으로 2차 창작물을 생성하고 상업적으로 이용할 수 있습니다.
- **핵심 가치**: 작가의 화풍에 대한 저작권을 명확히 보호하고, 합법적이고 투명한 AI 창작 생태계를 구축합니다.
- **해결 문제**: AI 이미지 생성 시 발생하는 원작자의 저작권 침해 문제를 해결하고, 작가에게 새로운 수익 창출 기회를 제공합니다.

---

## 2. 아키텍처 및 기술 스택

### 2.1. 전체 시스템 구조

본 프로젝트는 다음과 같은 주요 컴포넌트로 구성된 Monorepo 기반의 MSA(Microservice Architecture) 구조를 가집니다.

```
┌──────────┐      ┌───────────┐      ┌────────────────┐
│          │      │           │      │                │
│ Frontend ├─────►│  Backend  ├─────►│ Message Queue  │
│ (Vue.js) │      │ (Django)  │      │  (RabbitMQ)    │
│          │      │           │      │                │
└──────────┘      └─────┬─────┘      └──────┬─────────┘
                        │                   │
                        │                   │
              ┌─────────▼─────────┐  ┌──────▼─────────┐
              │                   │  │                │
              │    Database       │  │   AI Servers   │
              │   (PostgreSQL)    │  │ (Training/Infer)
              │                   │  │                │
              └───────────────────┘  └────────────────┘
```

- **Frontend**: 사용자와의 상호작용을 담당하는 Vue 3 기반의 싱글 페이지 애플리케이션(SPA)입니다.
- **Backend**: Django 기반의 REST API 서버로, 비즈니스 로직, 인증, 데이터 관리를 총괄합니다.
- **AI Servers**:
    - **Training Server**: 작가가 업로드한 이미지로 LoRA 모델을 학습(Fine-tuning)합니다.
    - **Inference Server**: 학습된 모델을 사용하여 사용자 요청에 따라 이미지를 생성합니다.
- **Message Queue**: RabbitMQ를 사용하여 Backend와 AI 서버 간의 비동기 작업을 안정적으로 처리합니다. (모델 학습, 이미지 생성)
- **Database**: PostgreSQL을 사용하여 모든 데이터를 관리합니다.

### 2.2. 핵심 기술 스택

| 구분 | 기술 | 선정 이유 |
|---|---|---|
| **Frontend** | Vue 3 (JavaScript) | 낮은 러닝 커브, Composition API의 유연성, 빠른 프로토타이핑. |
| **Backend** | Django | Python AI/ML 생태계와 통합이 용이하며, Admin 패널을 기본 제공. |
| **Database** | PostgreSQL | ACID 보장, 복잡한 관계형 데이터 및 JSON 필드 지원. |
| **Message Queue** | RabbitMQ | 장시간 소요되는 AI 작업을 안정적으로 비동기 처리. |
| **AI Model** | Stable Diffusion (LoRA) | 오픈소스이며, LoRA Fine-tuning을 지원하여 효율적인 모델 학습 가능. |
| **Infra** | Docker, GCP | 개발/운영 환경 일관성을 유지하고, GPU 서버를 유연하게 관리. |

### 2.3. 주요 데이터 흐름

- **모델 학습**: 작가 이미지 업로드 → Backend가 검증 후 RabbitMQ에 작업 전송 → Training Server가 모델 학습 후 Cloud Storage에 저장.
- **이미지 생성**: 사용자 프롬프트 입력 → Backend가 토큰 차감 후 RabbitMQ에 작업 전송 → Inference Server가 이미지 생성 후 Cloud Storage에 저장.

---

## 3. 핵심 비즈니스 로직 및 규칙

### 3.1. 화풍(Style) 생성
- **작가당 1개 스타일 제한**: MVP 단계에서는 작가 1명당 1개의 스타일만 생성할 수 있습니다.
- **학습 이미지**: 최소 10장, 최대 100장 (JPG, PNG, 512x512px 이상, 10MB 이하/장)
- **태그**: 모든 태그는 **영어**로만 입력해야 합니다.
- **스타일 이름 자동 태그화**: 스타일 생성 시 title이 모든 학습 이미지에 소문자 태그로 자동 등록됩니다.
  - 예: "Watercolor Dreams" → "watercolor dreams" 태그 자동 생성
- **학습 진행 상황 추적**:
  - 상태: `pending` → `training` → `completed`/`failed`
  - Training Server는 30초마다 Backend에 진행 상황 전송
  - Frontend는 5초마다 폴링하여 표시 (최대 30초 지연)
- **수정 불가**: 학습 완료된 모델은 삭제할 수 없습니다.

### 3.2. 이미지 생성
- **토큰 기반**: 각 스타일별로 작가가 설정한 토큰이 차감됩니다.
- **프롬프트**: 태그 기반의 **영어** 키워드로 작성해야 합니다.
- **지원 이미지 비율**:
  - 기본형 (1:1, 512×512px)
  - 그리드형 (2:2, 1024×1024px)
  - 세로형 (1:2, 512×1024px)
- **서명 강제 삽입**: 모든 생성 이미지에 작가 서명이 자동으로 삽입되며, 제거할 수 없습니다.
- **생성 진행 상황 추적**:
  - 상태: `queued` → `processing` → `completed`/`failed`
  - Inference Server는 주요 단계마다 Backend에 진행 상황 전송
  - Frontend는 5초마다 폴링하여 표시
- **실패 시**: 자동 재시도 최대 3회, 모두 실패 시 토큰 환불 + 알림
- **소유권**: 생성된 이미지의 소유권은 생성한 사용자에게 있으며, My Page에서 관리됩니다.

### 3.3. 토큰 시스템
- **웰컴 토큰**: 신규 가입 시 100 토큰이 무료로 지급됩니다.
- **토큰 구매**: 서버에 정의된 패키지 단위(예: 100, 500, 1000 토큰)로 구매할 수 있습니다.
- **가격 설정**: 작가는 자신의 스타일에 대해 '이미지 1장당 생성 비용'을 직접 설정합니다.
- **실패 시 환불**: 이미지 생성 실패 시, 소모된 토큰은 자동으로 환불됩니다.

### 3.4. 저작권 보호
- **서명 강제 삽입**: 모든 생성물에 작가 서명을 삽입하여 원작자를 명시합니다.
- **메타데이터**: 생성된 이미지 파일에 작가 ID, 스타일 ID, 생성 시간을 기록합니다.
- **삭제 불가 정책**:
  - 사용 중인 스타일을 가진 작가는 탈퇴 불가 (계정 비활성화 처리)
  - 스타일에 연결된 generations가 있으면 스타일 삭제 불가 (DB: ON DELETE RESTRICT)

### 3.5. 인증 및 권한
- **Google OAuth**: 인증은 Google 소셜 로그인을 통해서만 이루어집니다.
- **권한**: 모든 사용자는 'user' 권한으로 가입하며, 별도 신청을 통해 'artist' 권한을 얻을 수 있습니다.

### 3.6. 주요 MVP 제외 기능
- **정산 시스템**: 작가가 번 토큰을 현금으로 환전하는 기능은 포함되지 않습니다.
- **고급 커뮤니티**: 작가 랭킹, 추천 시스템, 이미지 신고 기능 등은 제외됩니다.
- **알림 고도화**: 실시간 푸시 알림, 이메일 알림은 제외됩니다. (웹 내 알림만 제공)

### 3.7. API 그룹 개요

프로젝트는 7개의 API 그룹으로 구성됩니다:

| 그룹 | 엔드포인트 | 주요 기능 |
|------|-----------|----------|
| **인증** | `/api/auth/*` | Google OAuth, 로그인/로그아웃 |
| **사용자** | `/api/users/*` | 프로필 조회/수정, 작가 권한 신청 |
| **토큰** | `/api/tokens/*` | 잔액 조회, 구매, 거래 내역 |
| **화풍** | `/api/styles/*` | 스타일 생성/조회/수정, 학습 진행 |
| **생성** | `/api/generations/*` | 이미지 생성 요청/조회, 공개 피드 |
| **커뮤니티** | `/api/users/:id/follow`, `/api/generations/:id/like` | 팔로우, 좋아요, 댓글 |
| **검색/알림** | `/api/search`, `/api/notifications` | 통합 검색, 알림 목록 |

**핵심 인증 플로우:**
1. `GET /api/auth/google/login` → Google OAuth 시작
2. Google 동의 → Callback `/api/auth/google/callback`
3. Backend → 세션 쿠키 설정
4. 이후 모든 요청 → 세션 쿠키 자동 포함

> 전체 API 명세: [docs/API.md](./docs/API.md)

### 3.8. 에러 코드 체계

#### HTTP 상태 코드
- `200 OK`, `201 Created`: 성공
- `400 Bad Request`: 잘못된 요청
- `401 Unauthorized`: 인증 필요
- `402 Payment Required`: 토큰 부족
- `403 Forbidden`: 권한 없음
- `404 Not Found`: 리소스 없음
- `409 Conflict`: 리소스 충돌 (중복 팔로우 등)
- `422 Unprocessable`: 검증 실패
- `429 Too Many Requests`: Rate Limit 초과
- `500 Server Error`: 서버 오류

#### 주요 애플리케이션 에러 코드
- **인증/권한**: `UNAUTHORIZED`, `FORBIDDEN`, `ARTIST_ONLY`
- **토큰**: `INSUFFICIENT_TOKENS`, `PAYMENT_FAILED`
- **스타일**: `STYLE_LIMIT_REACHED`, `STYLE_NOT_READY`, `TRAINING_FAILED`
- **이미지**: `INVALID_IMAGE_FORMAT`, `IMAGE_SIZE_EXCEEDED`, `GENERATION_FAILED`
- **커뮤니티**: `DUPLICATE_FOLLOW`, `SELF_FOLLOW_NOT_ALLOWED`, `REPLY_DEPTH_EXCEEDED`

> 전체 에러 코드 목록: [docs/API.md - Error Codes](./docs/API.md#error-codes)

### 3.9. 보안 설계 핵심

#### 인증 보안
- **Google OAuth only** (자체 로그인 없음)
- **세션 쿠키**: httponly, secure (HTTPS), samesite=lax

#### 데이터 보호
- **Google Secret Manager**: SECRET_KEY, OAUTH_CLIENT_SECRET, INTERNAL_API_TOKEN, TOSS_SECRET_KEY
- **Cloud Storage 접근 제어**: 서비스 계정 IAM 권한 (Storage objectAdmin)
  - 학습 이미지: Private (작가만 접근)
  - 생성 이미지: Public 읽기 (서명 포함)
  - 모델 파일: Private

#### Rate Limiting
- 이미지 생성: 6회/분/사용자
- API 전체: 100회/분/사용자
- 로그인 시도: 5회/5분/IP

#### 입력 검증
- Backend: DRF Serializer 검증
- Frontend: Zod 런타임 검증
- 프롬프트: XSS 방지 (HTML 태그 제거)

> 상세: [docs/SECURITY.md](./docs/SECURITY.md) (예정)

### 3.10. 성능 목표

| 지표 | 목표 |
|------|------|
| API 응답 시간 (p95) | < 500ms |
| 이미지 생성 시간 | < 10초/장 |
| 모델 학습 시간 | < 30분 (10장 기준) |
| 동시 접속자 | 100명 이상 |

#### 최적화 전략
- **DB 인덱스**: `User.google_id`, `StyleModel.training_status`, `(user_id, created_at)` 복합 인덱스
- **쿼리 최적화**: `select_related` (FK), `prefetch_related` (M:N), Cursor-based Pagination
- **캐싱 컬럼**: `follower_count` (artists), `like_count`, `comment_count` (generations)
- **이미지 최적화**: 학습 이미지 512x512 리사이즈, 생성 이미지 WebP 변환 (선택)

> 상세: [TECHSPEC.md Section 12 - 성능 및 확장성](./TECHSPEC.md#12-성능-및-확장성)

### 3.11. 테스트 전략

#### 테스트 피라미드
- **E2E (10%)**: Playwright - 로그인 → 이미지 생성 → 다운로드 등 Critical Path
- **통합 (20%)**: API Integration Tests - 모든 엔드포인트 응답 테스트
- **단위 (70%)**: Unit Tests - Service, Model, Composables

#### Coverage 목표
- Backend (pytest, pytest-django): **80%**
- Frontend (Vitest, @testing-library/vue): **70%**

#### AI 서버 테스트
- Unit: 이미지 전처리, 서명 삽입
- Integration: RabbitMQ Consumer, Backend Webhook
- Manual: 실제 10장 학습 후 품질 확인

> 상세: [TECHSPEC.md Section 13 - 테스트 전략](./TECHSPEC.md#13-테스트-전략)

---

## 4. 프론트엔드 페이지 구성

⚠️ **명세 준수 필수**: 아래 페이지 목록은 TECHSPEC.md Section 7.2에 정의된 필수 페이지입니다. PLAN.md 작성 또는 구현 시 반드시 검증하세요.

### 4.1. 필수 페이지 목록 (MVP)

1. **Main Page** (`/` 또는 `/community`)
   - 플랫폼 메인 / 공개 피드 그리드
   - 무한 스크롤, 좋아요/댓글 수 표시

2. **Feed Detail Page** (`/community/:id`)
   - 개별 피드(이미지)의 상세보기
   - **Comment Modal**: 댓글 목록 및 작성

3. **Search & Following Artist Page** (`/marketplace` 또는 `/search`)
   - **상단**: 검색창 (태그 기반 스타일 검색, 작가 이름 검색)
   - **정렬 옵션**: 최신순(recent), 인기순(popular - 팔로워 많은 작가 우선)
   - **팔로잉 섹션**: 내가 팔로잉한 작가들의 스타일 목록 (고정 영역)
   - **전체 스타일 그리드**: 검색 결과 또는 전체 스타일 목록

4. **Style Detail Page** (`/styles/:id` 또는 `/models/:id`)
   - 특정 스타일(작가)의 상세 정보
   - 작가 프로필, 샘플 이미지 갤러리
   - **이미지 생성 화면**: 프롬프트 입력, 비율 선택, 생성 버튼

5. **My Page** (`/profile` 또는 `/mypage`)
   - 정보 수정, 스타일 관리 페이지
   - 결제 페이지 이동 버튼
   - **공개/비공개 피드 그리드**: 내가 생성한 이미지 목록

6. **Edit / Create Style Page** (`/styles/create`)
   - 새로운 화풍(모델) 생성 / 업로드
   - 가격, 설명 수정
   - 학습 이미지 10~100장 업로드
   - 태그 입력, 서명 업로드

7. **Edit Profile** (`/profile/edit`)
   - 사용자 프로필 및 정보 수정
   - 닉네임, 프로필 이미지 등

8. **Payment Page** (`/payment` 또는 `/tokens`)
   - 토큰 결제 내역
   - 토큰 사용 내역 조회
   - 토큰 구매 (패키지 선택)

9. **Notification Page** (`/notifications`)
   - 알림 내역 조회 및 읽음 처리
   - 알림 유형: 좋아요, 댓글, 모델 학습 완료/실패, 생성 완료/실패

### 4.2. 공통 컴포넌트
- Header: 로그인 상태, 토큰 잔액, 알림 아이콘
- Footer: 저작권, 이용약관, 개인정보처리방침
- Modal: Comment, Image Preview
- Card: ModelCard, FeedItem

> **상세 페이지 구성**: [TECHSPEC.md Section 7.2 - 주요 페이지 구성](./TECHSPEC.md#72-주요-페이지-구성)

---

## 5. 개발 가이드 및 상세 문서 링크

### 5.1. Monorepo 코드 구조

프로젝트 코드는 `apps` 디렉터리 내에 각 서버별로 나뉘어 관리됩니다.

- `apps/backend/`: Django API 서버 코드
- `apps/frontend/`: Vue.js 프론트엔드 코드
- `apps/training-server/`: 모델 학습 서버 코드
- `apps/inference-server/`: 이미지 생성(추론) 서버 코드

각 디렉터리에는 자체적인 `README.md`와 `CODE_GUIDE.md`가 있어 해당 애플리케이션의 상세한 아키텍처와 코드 스타일을 확인할 수 있습니다.

### 5.2. 로컬 개발 환경

프로젝트 루트의 `docker-compose.yml` 파일을 사용하여 모든 서비스를 로컬 환경에서 한 번에 실행할 수 있습니다.

```bash
# 프로젝트 루트 디렉터리에서 실행
docker-compose up -d
```

상세 설정은 루트의 `DOCKER.md` 문서를 참고하세요.

### 5.3. 상세 문서 링크

더 상세한 정보가 필요할 경우 다음 문서를 참조하세요.

- **[전체 기술 명세 (원본)](./TECHSPEC.md)**: 이 요약 문서의 원본이 되는 전체 기술 명세서입니다.
- **[전체 API 명세](./docs/API.md)**: 모든 API 엔드포인트, 요청/응답 형식, 에러 코드를 상세히 정의합니다.
- **[데이터베이스 설계](./docs/database/README.md)**: 전체 ERD, 테이블 스키마, 설계 원칙을 포함합니다.
- **[공통 코드 패턴](./docs/PATTERNS.md)**: API 응답 형식, RabbitMQ 메시지 포맷 등 공통 패턴을 정의합니다.
- **각 애플리케이션별 `README.md`**: `apps/*/README.md`에서 각 서버의 아키텍처와 배포 방법을 확인할 수 있습니다.

---

## 📝 이 요약 문서의 사용 방법

### AI 에이전트 (Claude) 사용 시
1. **첫 작업 시작 전**: 이 TECHSPEC_SUMMARY.md를 먼저 읽어 프로젝트 전체 구조 파악
2. **필수 확인 사항**:
   - **Section 4**: 프론트엔드 페이지 9개 목록 확인 (페이지 누락 방지!)
   - **Section 3.7**: API 그룹 7개 확인 (API 누락 방지!)
   - **Section 3.8**: 에러 코드 체계 확인 (일관된 에러 처리)
3. **상세 명세 필요 시**: 앵커 링크를 따라 TECHSPEC.md 해당 섹션 읽기

### 신규 개발자 온보딩 시
1. Section 1~2: 프로젝트 정체성 및 아키텍처 이해 (10분)
2. Section 3: 핵심 비즈니스 규칙 숙지 (20분)
3. Section 4: 프론트엔드 페이지 전체 맵 확인 (5분)
4. Section 5: 코드 구조 및 로컬 환경 설정 (10분)

총 **45분 내 프로젝트 핵심 파악 가능**
