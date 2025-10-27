# Frontend Application

## Overview
Vue 3 기반 SPA, Pinia 상태 관리, Tailwind CSS 스타일링

## Tech Stack
- Vue 3 (Composition API)
- Pinia
- Vue Router
- Axios
- Tailwind CSS
- Vue I18n

## Architecture

### Directory Structure
\```
src/
├── app/
│   ├── App.vue
│   └── main.js
├── pages/              # Route pages
├── features/           # Feature modules
│   ├── auth/
│   │   ├── ui/         # Components
│   │   ├── api/        # API calls
│   │   ├── store.js    # Pinia store
│   │   └── composables/
│   └── ...
├── shared/             # Shared resources
│   ├── ui/             # Common components
│   ├── api/            # API client
│   ├── composables/
│   └── i18n/
└── router/
\```

### Module Pattern (Feature-Sliced Design)
각 feature는 독립적인 모듈:
- `ui/`: Vue 컴포넌트
- `api/`: HTTP 요청 함수
- `store.js`: Pinia 스토어
- `composables/`: 재사용 로직

### State Management
Pinia stores:
- `useAuthStore`: 인증 상태
- `useModelsStore`: 스타일 모델
- `useGenerationStore`: 이미지 생성 큐

### Routing
- `/`: Home (Feed)
- `/styles`: Marketplace
- `/styles/:id`: Style Detail
- `/generate`: Image Generation (requiresAuth)
- `/styles/create`: Create Style (requiresArtist)

## Development

### Setup
\```bash
npm install
npm run dev
\```

### Build
\```bash
npm run build
\```

### Test
\```bash
npm run test
npm run test:e2e
\```

## Key Decisions
- **JavaScript over TypeScript**: 빠른 프로토타이핑 우선
- **Feature-Sliced Design**: 확장 가능한 모듈 구조
- **Tailwind CSS**: 유틸리티 퍼스트 스타일링

## References
- [Task Plan](PLAN.md)
- [Code Guide](GUIDE.md)
- [API Spec](../../docs/API.md)
- [Design System](../../design/README.md)