# Frontend Application

## Overview

Vue 3 기반의 Style License 클라이언트 애플리케이션입니다. Feature-Sliced Design 패턴을 적용하여 확장 가능한 구조로 설계되었으며, Pinia 상태 관리, Vue Router 기반 라우팅, Tailwind CSS 스타일링을 사용합니다.

**핵심 역할:**
- 9개 주요 페이지 제공 (메인, 검색, 스타일 상세, 마이페이지 등)
- RESTful API 통신 (Backend와 세션 기반 인증)
- 반응형 SPA (Single Page Application)
- 다국어 지원 (한국어/영어)

---

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Framework | Vue 3 | 3.3+ | UI Framework (Composition API) |
| State Management | Pinia | 2.1+ | 상태 관리 |
| Routing | Vue Router | 4.2+ | 클라이언트 라우팅 |
| HTTP Client | Axios | 1.6+ | API 통신 |
| Styling | Tailwind CSS | 3.4+ | 유틸리티 퍼스트 CSS |
| i18n | Vue I18n | 9.8+ | 다국어 처리 |
| Build Tool | Vite | 5.0+ | 빌드 및 개발 서버 |
| Testing | Vitest | 1.0+ | Unit tests |
| E2E Testing | Playwright | 1.40+ | End-to-end tests |
| Validation | Zod | 3.22+ | 런타임 데이터 검증 |
| Code Quality | ESLint, Prettier | 8.56+, 3.1+ | Linting, Formatting |

> **참고**: TypeScript를 사용하지 않으며, Zod 런타임 검증과 ESLint로 코드 안정성을 확보합니다.

---

## Directory Structure

```
apps/frontend/
├── public/                   # 정적 파일
│   ├── favicon.ico
│   └── fonts/
│
├── src/
│   ├── app/                  # 앱 진입점
│   │   ├── App.vue          # 루트 컴포넌트
│   │   ├── main.js          # Entry point
│   │   └── styles/          # 글로벌 스타일
│   │
│   ├── pages/               # 페이지 컴포넌트 (라우트 매칭)
│   │   ├── MainPage.vue     # 메인 (공개 피드)
│   │   ├── FeedDetailPage.vue  # 피드 상세
│   │   ├── SearchPage.vue    # 검색 & 팔로잉
│   │   ├── StyleDetailPage.vue # 스타일 상세 & 생성
│   │   ├── MyPage.vue        # 마이페이지
│   │   ├── EditStylePage.vue # 스타일 생성/수정
│   │   ├── EditProfilePage.vue # 프로필 수정
│   │   ├── PaymentPage.vue   # 토큰 결제 내역
│   │   └── NotificationPage.vue # 알림
│   │
│   ├── features/            # Feature 모듈 (Feature-Sliced Design)
│   │   ├── auth/
│   │   │   ├── ui/          # 로그인, 회원가입 컴포넌트
│   │   │   ├── api/         # 인증 API 함수
│   │   │   ├── store.js     # useAuthStore (Pinia)
│   │   │   └── composables/ # useAuth 훅
│   │   │
│   │   ├── styles/          # 스타일 모델 관리
│   │   │   ├── ui/          # 스타일 카드, 상세, 생성 폼
│   │   │   ├── api/         # 스타일 CRUD API
│   │   │   ├── store.js     # useStylesStore
│   │   │   └── composables/ # useStyleForm, useStyleDetail
│   │   │
│   │   ├── generation/      # 이미지 생성
│   │   │   ├── ui/          # 생성 폼, 진행률, 결과 표시
│   │   │   ├── api/         # 생성 요청 API
│   │   │   ├── store.js     # useGenerationStore
│   │   │   └── composables/ # useGenerationQueue
│   │   │
│   │   ├── community/       # 커뮤니티 기능
│   │   │   ├── ui/          # 좋아요, 댓글, 팔로우 컴포넌트
│   │   │   ├── api/         # 소셜 기능 API
│   │   │   ├── store.js     # useCommunityStore
│   │   │   └── composables/ # useComments, useFollow
│   │   │
│   │   ├── tokens/          # 토큰 시스템
│   │   │   ├── ui/          # 토큰 잔액, 구매 컴포넌트
│   │   │   ├── api/         # 토큰 API
│   │   │   ├── store.js     # useTokensStore
│   │   │   └── composables/ # useTokenBalance
│   │   │
│   │   ├── search/          # 검색 기능
│   │   │   ├── ui/          # 검색창, 필터
│   │   │   ├── api/         # 검색 API
│   │   │   └── composables/ # useSearch
│   │   │
│   │   └── notifications/   # 알림 시스템
│   │       ├── ui/          # 알림 목록, 뱃지
│   │       ├── api/         # 알림 API
│   │       ├── store.js     # useNotificationsStore
│   │       └── composables/ # useNotifications
│   │
│   ├── shared/              # 공유 리소스
│   │   ├── ui/              # 공통 컴포넌트
│   │   │   ├── Button.vue
│   │   │   ├── Modal.vue
│   │   │   ├── Input.vue
│   │   │   ├── Card.vue
│   │   │   └── ...
│   │   │
│   │   ├── api/             # API 클라이언트
│   │   │   ├── client.js   # Axios 인스턴스
│   │   │   └── interceptors.js # 인증, 에러 처리
│   │   │
│   │   ├── composables/     # 공통 훅
│   │   │   ├── usePagination.js
│   │   │   ├── useInfiniteScroll.js
│   │   │   ├── useDebounce.js
│   │   │   └── useToast.js
│   │   │
│   │   ├── i18n/            # 다국어 리소스
│   │   │   ├── ko.json
│   │   │   └── en.json
│   │   │
│   │   ├── utils/           # 유틸리티 함수
│   │   │   ├── format.js   # 날짜, 숫자 포맷팅
│   │   │   ├── validation.js # Zod 스키마
│   │   │   └── constants.js
│   │   │
│   │   └── assets/          # 이미지, 아이콘
│   │
│   └── router/              # 라우팅 설정
│       ├── index.js         # 라우터 인스턴스
│       ├── routes.js        # 라우트 정의
│       └── guards.js        # 네비게이션 가드
│
├── tests/                   # 테스트
│   ├── unit/                # Unit tests
│   ├── component/           # Component tests
│   └── e2e/                 # E2E tests (Playwright)
│
├── .env.example             # 환경변수 템플릿
├── vite.config.js           # Vite 설정
├── tailwind.config.js       # Tailwind 설정
├── vitest.config.js         # Vitest 설정
├── playwright.config.js     # Playwright 설정
├── eslint.config.js         # ESLint 설정
├── .prettierrc              # Prettier 설정
├── package.json
├── PLAN.md                  # 개발 작업 계획
├── CODE_GUIDE.md            # 코드 작성 패턴
└── README.md                # This file
```

---

## Architecture

### Feature-Sliced Design 패턴

각 feature는 독립적인 모듈로 구성되어 확장 가능성을 높입니다.

```
Feature 구조:
feature/
├── ui/           # Vue 컴포넌트 (presentational)
├── api/          # HTTP 요청 함수
├── store.js      # Pinia 스토어 (상태 관리)
└── composables/  # 재사용 가능한 로직 (hooks)
```

**장점**:
- 도메인별 독립성 보장
- 테스트 용이성
- 팀 협업 시 충돌 최소화

---

### 주요 페이지 구성

| 페이지 | 경로 | 인증 | 설명 |
|-------|------|------|------|
| **Main Page** | `/` | 선택 | 공개 피드 그리드 (무한 스크롤) |
| **Feed Detail** | `/feed/:id` | 선택 | 이미지 상세 + 댓글 모달 |
| **Search** | `/search` | 선택 | 스타일/작가 검색 + 팔로잉 목록 |
| **Style Detail** | `/styles/:id` | 선택 | 스타일 정보 + 이미지 생성 폼 |
| **My Page** | `/me` | 필수 | 정보 수정, 스타일/피드 관리 |
| **Edit Style** | `/styles/create`, `/styles/:id/edit` | 작가 | 스타일 생성/수정 (이미지 업로드) |
| **Edit Profile** | `/me/edit` | 필수 | 프로필 정보 수정 |
| **Payment** | `/me/tokens` | 필수 | 토큰 구매 내역/사용 내역 |
| **Notification** | `/notifications` | 필수 | 알림 목록 + 읽음 처리 |

---

### 상태 관리 전략

Pinia 스토어를 도메인별로 분리하여 관리합니다.

**주요 스토어**:

```javascript
// 1. useAuthStore (인증)
{
  user: null,              // 현재 로그인 사용자
  isAuthenticated: false,  // 인증 여부
  role: 'user',            // 'user' | 'artist'

  actions: {
    login(), logout(), checkSession()
  }
}

// 2. useStylesStore (스타일 모델)
{
  styles: [],              // 스타일 목록
  myStyles: [],            // 내 스타일
  currentStyle: null,      // 상세 페이지 스타일

  actions: {
    fetchStyles(), createStyle(), updateStyle(), deleteStyle()
  }
}

// 3. useGenerationStore (이미지 생성)
{
  queue: [],               // 생성 대기열
  history: [],             // 생성 이력
  currentGeneration: null, // 진행 중인 생성

  actions: {
    requestGeneration(), pollProgress(), fetchHistory()
  }
}

// 4. useCommunityStore (커뮤니티)
{
  feed: [],                // 공개 피드
  following: [],           // 팔로잉 목록

  actions: {
    fetchFeed(), toggleLike(), followUser(), unfollowUser()
  }
}
```

**전역 상태 최소화**:
- 세션 정보(`useAuthStore`)
- 테마/언어 설정 (필요 시)
- 그 외는 페이지별 로컬 상태 사용

---

### 라우팅 전략

**인증 가드**:
```javascript
// router/guards.js
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // 인증 필요 라우트
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next('/login')
  }

  // 작가 전용 라우트
  if (to.meta.requiresArtist && authStore.role !== 'artist') {
    return next('/')
  }

  next()
})
```

**지연 로딩**:
```javascript
// router/routes.js
const routes = [
  {
    path: '/styles/:id',
    component: () => import('@/pages/StyleDetailPage.vue'), // 지연 로딩
    meta: { requiresAuth: false }
  },
  {
    path: '/styles/create',
    component: () => import('@/pages/EditStylePage.vue'),
    meta: { requiresAuth: true, requiresArtist: true }
  }
]
```

---

### API 통신 패턴

**Axios Interceptor** 사용:

```javascript
// shared/api/interceptors.js
// Request Interceptor - 세션 쿠키 자동 포함
axios.interceptors.request.use(config => {
  config.withCredentials = true  // 세션 쿠키 전송
  return config
})

// Response Interceptor - 에러 처리
axios.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // 인증 만료 시 로그인 페이지로
      router.push('/login')
    }
    return Promise.reject(error)
  }
)
```

**API 함수 예시**:
```javascript
// features/styles/api/index.js
export const fetchStyles = async (params) => {
  const response = await axios.get('/api/styles', { params })
  return response.data
}

export const createStyle = async (data) => {
  const response = await axios.post('/api/styles', data)
  return response.data
}
```

---

### Data Flow

#### 이미지 생성 플로우
```
사용자 (StyleDetailPage)
  ↓
useGenerationStore.requestGeneration()
  ↓
POST /api/generations (Backend)
  ↓
RabbitMQ → Inference Server
  ↓
Polling (매 5초): GET /api/generations/:id
  ↓
진행률 업데이트 (0% → 25% → 50% → 75% → 90% → 100%)
  ↓
생성 완료 → 이미지 URL 표시
```

#### 스타일 학습 플로우
```
작가 (EditStylePage)
  ↓
이미지 업로드 (10~100장)
  ↓
POST /api/styles (Backend)
  ↓
RabbitMQ → Training Server
  ↓
Polling (매 5초): GET /api/styles/:id
  ↓
진행률 업데이트 (progress JSONB 필드)
  ↓
학습 완료 (30분~2시간) → 알림 표시
```

---

## Development Setup

### Prerequisites
- Node.js 18+ 및 npm
- Backend 서버 실행 중 (http://localhost:8000)

### Installation

```bash
# 1. 프로젝트 이동
cd apps/frontend

# 2. 의존성 설치
npm install

# 3. 환경변수 설정
cp .env.example .env
# .env 파일 수정

# 4. 개발 서버 실행
npm run dev
```

### Environment Variables

```bash
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000

# S3 이미지 도메인 (선택사항)
VITE_S3_BASE_URL=https://stylelicense-media.s3.ap-northeast-2.amazonaws.com

# 기본 언어
VITE_DEFAULT_LOCALE=ko
```

---

## Development Workflow

### Running Dev Server

```bash
# 개발 서버 시작 (Hot Module Replacement)
npm run dev

# 특정 포트 지정
npm run dev -- --port 3000
```

### Building

```bash
# 프로덕션 빌드
npm run build

# 빌드 미리보기
npm run preview
```

### Testing

```bash
# Unit tests (Vitest)
npm run test

# Watch mode
npm run test:watch

# Coverage 리포트
npm run test:coverage

# E2E tests (Playwright)
npm run test:e2e

# E2E UI mode
npm run test:e2e:ui
```

### Code Quality

```bash
# Lint
npm run lint

# Lint + Fix
npm run lint:fix

# Format (Prettier)
npm run format
```

---

## Page Structure

### 1. Main Page (공개 피드)
- 모든 공개 생성물 그리드 표시
- 무한 스크롤 (cursor-based pagination)
- 태그 필터링
- 정렬: 최신순, 인기순

### 2. Feed Detail Page
- 이미지 상세 보기
- 댓글 모달 (1단계 대댓글 지원)
- 좋아요 기능
- 작가 정보 표시

### 3. Search & Following Artist Page
- **검색창**: 태그 기반 스타일 검색, 작가 이름 검색
- **정렬**: 최신순(recent), 인기순(popular)
- **팔로잉 섹션**: 내가 팔로잉한 작가들의 스타일 목록 (고정 영역)
- **전체 스타일 그리드**: 검색 결과 또는 전체 스타일 목록

### 4. Style Detail Page
- 스타일 정보 (작가명, 가격, 설명, 샘플 이미지)
- 이미지 생성 폼 (프롬프트 태그 입력, 비율 선택)
- 진행률 표시 (폴링)
- 생성 이력

### 5. My Page
- 프로필 정보 수정 버튼
- 내 스타일 관리 (작가인 경우)
- 공개/비공개 피드 그리드
- 토큰 결제 페이지 이동 버튼

### 6. Edit / Create Style Page
- 이미지 업로드 (10~100장, 드래그 앤 드롭)
- 스타일 이름, 설명, 가격 설정
- 학습 진행률 표시 (폴링)

### 7. Edit Profile
- 사용자 이름, 프로필 이미지 수정
- 작가 권한 신청 버튼

### 8. Payment Page
- 토큰 구매 내역 (결제 성공/실패)
- 토큰 사용 내역 (이미지 생성 이력)
- 토큰 구매 버튼 (토스 페이먼츠 연동)

### 9. Notification Page
- 알림 목록 (팔로우, 좋아요, 댓글, 생성 완료/실패, 학습 완료/실패)
- 읽음 처리
- 모든 알림 읽음 버튼

---

## State Management

### Composable 훅 활용

```javascript
// features/generation/composables/useGenerationQueue.js
export function useGenerationQueue() {
  const generationStore = useGenerationStore()
  const { queue } = storeToRefs(generationStore)

  const addToQueue = async (data) => {
    await generationStore.requestGeneration(data)
  }

  const pollProgress = async (generationId) => {
    const interval = setInterval(async () => {
      const result = await generationStore.fetchGeneration(generationId)
      if (result.status === 'completed' || result.status === 'failed') {
        clearInterval(interval)
      }
    }, 5000) // 5초마다 폴링
  }

  return { queue, addToQueue, pollProgress }
}
```

---

## Testing Strategy

### Test Types

| Type | Coverage | Tools | 설명 |
|------|----------|-------|------|
| Unit Tests | 70% | Vitest | Composables, Stores, Utils |
| Component Tests | 20% | Vitest + Testing Library | UI 컴포넌트 렌더링/이벤트 |
| E2E Tests | 10% | Playwright | 핵심 사용자 플로우 |

**Test Fixtures**: `tests/fixtures/`
**Coverage Goal**: 80%

### Unit Test 예시

```javascript
// tests/unit/composables/useAuth.test.js
import { describe, it, expect } from 'vitest'
import { useAuth } from '@/features/auth/composables/useAuth'

describe('useAuth', () => {
  it('should login successfully', async () => {
    const { login, isAuthenticated } = useAuth()
    await login({ email: 'test@example.com', password: 'password' })
    expect(isAuthenticated.value).toBe(true)
  })
})
```

---

## Deployment

### Production Checklist

- [ ] 환경변수 설정 (`VITE_API_BASE_URL=https://stylelicense.com`)
- [ ] 빌드 오류 없음 (`npm run build`)
- [ ] E2E 테스트 통과 (`npm run test:e2e`)
- [ ] Lint 통과 (`npm run lint`)
- [ ] Backend EC2 Nginx 디렉토리 생성 (`/var/www/stylelicense/frontend/`)
- [ ] DNS 설정 확인 (A 레코드: stylelicense.com → EC2 Public IP)
- [ ] CORS 설정 확인 (Backend)
- [ ] CSP 헤더 설정 (Nginx)

### Deployment to Backend EC2 (Nginx Static Files)

```bash
# 1. 프로덕션 빌드
npm run build

# 2. Backend EC2로 전송 (SCP)
scp -r dist/* ubuntu@stylelicense.com:/var/www/stylelicense/frontend/

# 3. Nginx 재시작 (필요 시)
ssh ubuntu@stylelicense.com 'sudo systemctl reload nginx'
```

**빌드 결과**: `dist/` 폴더 (정적 파일)

**Nginx 설정 예시** (Backend EC2의 `/etc/nginx/sites-available/stylelicense`):
```nginx
server {
    listen 443 ssl http2;
    server_name stylelicense.com;

    # Frontend 정적 파일 (SPA)
    location / {
        root /var/www/stylelicense/frontend;
        try_files $uri $uri/ /index.html;

        # 캐싱 설정 (정적 파일 최적화)
        location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API 프록시
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

**자동화**: GitHub Actions에서 자동 실행됨 (`.github/workflows/frontend.yml`)

---

## Monitoring

### Metrics to Monitor

- 페이지 로드 시간 (FCP, LCP)
- API 응답 시간
- JavaScript 에러 발생 빈도
- 사용자 플로우 완료율 (회원가입 → 생성 → 결제)

### Tools

- **Google Analytics**: 페이지뷰, 사용자 행동
- **Sentry**: JavaScript 에러 추적
- **Nginx 로그**: Backend EC2의 `/var/log/nginx/access.log` 분석

---

## References

### 필수 문서
- **[CODE_GUIDE.md](CODE_GUIDE.md)** - 코드 작성 패턴 및 예제 (코드 작성 전 필독)
- **[PLAN.md](PLAN.md)** - 개발 작업 계획 (다음 작업 확인)

### 프로젝트 문서
- **[TECHSPEC.md](../../TECHSPEC.md)** - 전체 시스템 아키텍처
- **[docs/API.md](../../docs/API.md)** - Backend API 명세
- **[docs/PATTERNS.md](../../docs/PATTERNS.md)** - 공통 코드 패턴

### 외부 문서
- **Vue 3**: https://vuejs.org/guide/introduction.html
- **Pinia**: https://pinia.vuejs.org/
- **Vue Router**: https://router.vuejs.org/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Vite**: https://vitejs.dev/guide/

---

## Troubleshooting

### Common Issues

**1. CORS 오류**
```bash
# Backend CORS 설정 확인
# CORS_ALLOWED_ORIGINS에 http://localhost:5173 포함되어 있는지 확인
```

**2. 세션 쿠키가 전송되지 않음**
```javascript
// Axios 설정 확인
axios.defaults.withCredentials = true
```

**3. Node 버전 오류**
```bash
# Node.js 버전 확인 (18+ 필요)
node -v

# nvm 사용 시
nvm use 18
```

**4. Vite 빌드 오류 (메모리 부족)**
```bash
# Node 메모리 증가
export NODE_OPTIONS=--max-old-space-size=4096
npm run build
```

**5. E2E 테스트 실패**
```bash
# Playwright 브라우저 설치
npx playwright install

# Headless 모드 비활성화
npm run test:e2e -- --headed
```

---

## Support

- **GitHub Issues**: 버그 리포트 및 기능 제안
- **Team Communication**: Slack #frontend 채널
- **Documentation**: [TECHSPEC.md](../../TECHSPEC.md)
