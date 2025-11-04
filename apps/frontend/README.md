# Frontend Application

## Overview

Style License client application based on Vue 3. Designed with a scalable architecture using the Feature-Sliced Design pattern, with Pinia state management, Vue Router-based routing, and Tailwind CSS styling.

**Core Responsibilities:**
- Provide 9 main pages (Main, Search, Style Detail, My Page, etc.)
- RESTful API communication (Session-based authentication with Backend)
- Responsive SPA (Single Page Application)
- Multi-language support (Korean/English)

---

## Tech Stack

| Category | Technology | Version | Purpose |
|----------|------------|---------|---------|
| Framework | Vue 3 | 3.3+ | UI Framework (Composition API) |
| State Management | Pinia | 2.1+ | State management |
| Routing | Vue Router | 4.2+ | Client routing |
| HTTP Client | Axios | 1.6+ | API communication |
| Styling | Tailwind CSS | 3.4+ | Utility-first CSS |
| i18n | Vue I18n | 9.8+ | Multi-language support |
| Build Tool | Vite | 5.0+ | Build and dev server |
| Testing | Vitest | 1.0+ | Unit tests |
| E2E Testing | Playwright | 1.40+ | End-to-end tests |
| Validation | Zod | 3.22+ | Runtime data validation |
| Code Quality | ESLint, Prettier | 8.56+, 3.1+ | Linting, Formatting |

> **Note**: TypeScript is not used. Code stability is ensured through Zod runtime validation and ESLint.

---

## Directory Structure

```
apps/frontend/
├── public/                   # Static files
│   ├── favicon.ico
│   └── fonts/
│
├── src/
│   ├── app/                  # App entry point
│   │   ├── App.vue          # Root component
│   │   ├── main.js          # Entry point
│   │   └── styles/          # Global styles
│   │
│   ├── pages/               # Page components (route matching)
│   │   ├── MainPage.vue     # Main (public feed)
│   │   ├── FeedDetailPage.vue  # Feed detail
│   │   ├── SearchPage.vue    # Search & Following
│   │   ├── StyleDetailPage.vue # Style detail & generation
│   │   ├── MyPage.vue        # My page
│   │   ├── EditStylePage.vue # Create/edit style
│   │   ├── EditProfilePage.vue # Edit profile
│   │   ├── PaymentPage.vue   # Token payment history
│   │   └── NotificationPage.vue # Notifications
│   │
│   ├── features/            # Feature modules (Feature-Sliced Design)
│   │   ├── auth/
│   │   │   ├── ui/          # Login, signup components
│   │   │   ├── api/         # Auth API functions
│   │   │   ├── store.js     # useAuthStore (Pinia)
│   │   │   └── composables/ # useAuth hook
│   │   │
│   │   ├── styles/          # Style model management
│   │   │   ├── ui/          # Style card, detail, creation form
│   │   │   ├── api/         # Style CRUD API
│   │   │   ├── store.js     # useStylesStore
│   │   │   └── composables/ # useStyleForm, useStyleDetail
│   │   │
│   │   ├── generation/      # Image generation
│   │   │   ├── ui/          # Generation form, progress, results
│   │   │   ├── api/         # Generation request API
│   │   │   ├── store.js     # useGenerationStore
│   │   │   └── composables/ # useGenerationQueue
│   │   │
│   │   ├── community/       # Community features
│   │   │   ├── ui/          # Like, comment, follow components
│   │   │   ├── api/         # Social feature API
│   │   │   ├── store.js     # useCommunityStore
│   │   │   └── composables/ # useComments, useFollow
│   │   │
│   │   ├── tokens/          # Token system
│   │   │   ├── ui/          # Token balance, purchase components
│   │   │   ├── api/         # Token API
│   │   │   ├── store.js     # useTokensStore
│   │   │   └── composables/ # useTokenBalance
│   │   │
│   │   ├── search/          # Search functionality
│   │   │   ├── ui/          # Search bar, filters
│   │   │   ├── api/         # Search API
│   │   │   └── composables/ # useSearch
│   │   │
│   │   └── notifications/   # Notification system
│   │       ├── ui/          # Notification list, badge
│   │       ├── api/         # Notification API
│   │       ├── store.js     # useNotificationsStore
│   │       └── composables/ # useNotifications
│   │
│   ├── shared/              # Shared resources
│   │   ├── ui/              # Common components
│   │   │   ├── Button.vue
│   │   │   ├── Modal.vue
│   │   │   ├── Input.vue
│   │   │   ├── Card.vue
│   │   │   └── ...
│   │   │
│   │   ├── api/             # API client
│   │   │   ├── client.js   # Axios instance
│   │   │   └── interceptors.js # Auth, error handling
│   │   │
│   │   ├── composables/     # Common hooks
│   │   │   ├── usePagination.js
│   │   │   ├── useInfiniteScroll.js
│   │   │   ├── useDebounce.js
│   │   │   └── useToast.js
│   │   │
│   │   ├── i18n/            # Multi-language resources
│   │   │   ├── ko.json
│   │   │   └── en.json
│   │   │
│   │   ├── utils/           # Utility functions
│   │   │   ├── format.js   # Date, number formatting
│   │   │   ├── validation.js # Zod schemas
│   │   │   └── constants.js
│   │   │
│   │   └── assets/          # Images, icons
│   │
│   └── router/              # Routing configuration
│       ├── index.js         # Router instance
│       ├── routes.js        # Route definitions
│       └── guards.js        # Navigation guards
│
├── tests/                   # Tests
│   ├── unit/                # Unit tests
│   ├── component/           # Component tests
│   └── e2e/                 # E2E tests (Playwright)
│
├── .env.example             # Environment variables template
├── vite.config.js           # Vite configuration
├── tailwind.config.js       # Tailwind configuration
├── vitest.config.js         # Vitest configuration
├── playwright.config.js     # Playwright configuration
├── eslint.config.js         # ESLint configuration
├── .prettierrc              # Prettier configuration
├── package.json
├── PLAN.md                  # Development task plan
├── CODE_GUIDE.md            # Code writing patterns
└── README.md                # This file
```

---

## Architecture

### Feature-Sliced Design Pattern

Each feature is organized as an independent module to enhance scalability.

```
Feature structure:
feature/
├── ui/           # Vue components (presentational)
├── api/          # HTTP request functions
├── store.js      # Pinia store (state management)
└── composables/  # Reusable logic (hooks)
```

**Benefits**:
- Domain independence guaranteed
- Easy to test
- Minimize conflicts during team collaboration

---

### Main Page Configuration

| Page | Route | Auth | Description |
|------|------|------|-------------|
| **Main Page** | `/` | Optional | Public feed grid (infinite scroll) |
| **Feed Detail** | `/feed/:id` | Optional | Image detail + comment modal |
| **Search** | `/search` | Optional | Style/artist search + following list |
| **Style Detail** | `/styles/:id` | Optional | Style info + image generation form |
| **My Page** | `/me` | Required | Edit info, manage styles/feed |
| **Edit Style** | `/styles/create`, `/styles/:id/edit` | Artist | Create/edit style (image upload) |
| **Edit Profile** | `/me/edit` | Required | Edit profile information |
| **Payment** | `/me/tokens` | Required | Token purchase/usage history |
| **Notification** | `/notifications` | Required | Notification list + mark as read |

---

### State Management Strategy

Pinia stores are separated by domain.

**Main Stores**:

```javascript
// 1. useAuthStore (Authentication)
{
  user: null,              // Current logged-in user
  isAuthenticated: false,  // Authentication status
  role: 'user',            // 'user' | 'artist'

  actions: {
    login(), logout(), checkSession()
  }
}

// 2. useStylesStore (Style models)
{
  styles: [],              // Style list
  myStyles: [],            // My styles
  currentStyle: null,      // Detail page style

  actions: {
    fetchStyles(), createStyle(), updateStyle(), deleteStyle()
  }
}

// 3. useGenerationStore (Image generation)
{
  queue: [],               // Generation queue
  history: [],             // Generation history
  currentGeneration: null, // Current generation in progress

  actions: {
    requestGeneration(), pollProgress(), fetchHistory()
  }
}

// 4. useCommunityStore (Community)
{
  feed: [],                // Public feed
  following: [],           // Following list

  actions: {
    fetchFeed(), toggleLike(), followUser(), unfollowUser()
  }
}
```

**Minimize Global State**:
- Session info (`useAuthStore`)
- Theme/language settings (if needed)
- Everything else uses page-level local state

---

### Routing Strategy

**Authentication Guards**:
```javascript
// router/guards.js
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()

  // Routes requiring authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    return next('/login')
  }

  // Artist-only routes
  if (to.meta.requiresArtist && authStore.role !== 'artist') {
    return next('/')
  }

  next()
})
```

**Lazy Loading**:
```javascript
// router/routes.js
const routes = [
  {
    path: '/styles/:id',
    component: () => import('@/pages/StyleDetailPage.vue'), // Lazy loading
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

### API Communication Pattern

**Using Axios Interceptor**:

```javascript
// shared/api/interceptors.js
// Request Interceptor - Automatically include session cookie
axios.interceptors.request.use(config => {
  config.withCredentials = true  // Send session cookie
  return config
})

// Response Interceptor - Error handling
axios.interceptors.response.use(
  response => response.data,
  error => {
    if (error.response?.status === 401) {
      // Redirect to login on auth expiration
      router.push('/login')
    }
    return Promise.reject(error)
  }
)
```

**API Function Example**:
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

#### Image Generation Flow
```
User (StyleDetailPage)
  ↓
useGenerationStore.requestGeneration()
  ↓
POST /api/generations (Backend)
  ↓
RabbitMQ → Inference Server
  ↓
Polling (every 5 seconds): GET /api/generations/:id
  ↓
Progress update (0% → 25% → 50% → 75% → 90% → 100%)
  ↓
Generation complete → Display image URL
```

#### Style Training Flow
```
Artist (EditStylePage)
  ↓
Upload images (10~100 images)
  ↓
POST /api/styles (Backend)
  ↓
RabbitMQ → Training Server
  ↓
Polling (every 5 seconds): GET /api/styles/:id
  ↓
Progress update (progress JSONB field)
  ↓
Training complete (30min~2hours) → Show notification
```

---

## Development Setup

### Prerequisites
- Node.js 18+ and npm
- Backend server running (http://localhost:8000)

### Installation

```bash
# 1. Navigate to project
cd apps/frontend

# 2. Install dependencies
npm install

# 3. Set environment variables
cp .env.example .env
# Edit .env file

# 4. Run development server
npm run dev
```

### Environment Variables

```bash
# Backend API URL
VITE_API_BASE_URL=http://localhost:8000

# S3 image domain (optional)
VITE_S3_BASE_URL=https://stylelicense-media.s3.ap-northeast-2.amazonaws.com

# Default language
VITE_DEFAULT_LOCALE=ko
```

---

## Development Workflow

### Running Dev Server

```bash
# Start development server (Hot Module Replacement)
npm run dev

# Specify port
npm run dev -- --port 3000
```

### Building

```bash
# Production build
npm run build

# Preview build
npm run preview
```

### Testing

```bash
# Unit tests (Vitest)
npm run test

# Watch mode
npm run test:watch

# Coverage report
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

### 1. Main Page (Public Feed)
- Display all public generations in grid
- Infinite scroll (cursor-based pagination)
- Tag filtering
- Sort: Latest, Popular

### 2. Feed Detail Page
- Image detail view
- Comment modal (1-level reply support)
- Like feature
- Artist info display

### 3. Search & Following Artist Page
- **Search bar**: Tag-based style search, artist name search
- **Sort**: Latest (recent), Popular (popular)
- **Following section**: Styles from followed artists (fixed area)
- **All styles grid**: Search results or all styles list

### 4. Style Detail Page
- Style info (artist name, price, description, sample images)
- Image generation form (prompt tag input, aspect ratio selection)
- Progress display (polling)
- Generation history

### 5. My Page
- Edit profile button
- Manage my styles (if artist)
- Public/private feed grid
- Navigate to token payment page

### 6. Edit / Create Style Page
- Image upload (10~100 images, drag and drop)
- Set style name, description, price
- Display training progress (polling)

### 7. Edit Profile
- Edit username, profile image
- Artist permission application button

### 8. Payment Page
- Token purchase history (payment success/failure)
- Token usage history (image generation history)
- Token purchase button (Toss Payments integration)

### 9. Notification Page
- Notification list (follow, like, comment, generation complete/failed, training complete/failed)
- Mark as read
- Mark all as read button

---

## State Management

### Using Composable Hooks

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
    }, 5000) // Poll every 5 seconds
  }

  return { queue, addToQueue, pollProgress }
}
```

---

## Testing Strategy

### Test Types

| Type | Coverage | Tools | Description |
|------|----------|-------|-------------|
| Unit Tests | 70% | Vitest | Composables, Stores, Utils |
| Component Tests | 20% | Vitest + Testing Library | UI component rendering/events |
| E2E Tests | 10% | Playwright | Core user flows |

**Test Fixtures**: `tests/fixtures/`
**Coverage Goal**: 80%

### Unit Test Example

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

- [ ] Set environment variables (`VITE_API_BASE_URL=https://stylelicense.com`)
- [ ] No build errors (`npm run build`)
- [ ] E2E tests pass (`npm run test:e2e`)
- [ ] Lint passes (`npm run lint`)
- [ ] Create Backend EC2 Nginx directory (`/var/www/stylelicense/frontend/`)
- [ ] Verify DNS configuration (A record: stylelicense.com → EC2 Public IP)
- [ ] Verify CORS configuration (Backend)
- [ ] Set CSP headers (Nginx)

### Deployment to Backend EC2 (Nginx Static Files)

```bash
# 1. Production build
npm run build

# 2. Transfer to Backend EC2 (SCP)
scp -r dist/* ubuntu@stylelicense.com:/var/www/stylelicense/frontend/

# 3. Reload Nginx (if needed)
ssh ubuntu@stylelicense.com 'sudo systemctl reload nginx'
```

**Build output**: `dist/` folder (static files)

**Nginx configuration example** (Backend EC2's `/etc/nginx/sites-available/stylelicense`):
```nginx
server {
    listen 443 ssl http2;
    server_name stylelicense.com;

    # Frontend static files (SPA)
    location / {
        root /var/www/stylelicense/frontend;
        try_files $uri $uri/ /index.html;

        # Caching configuration (static file optimization)
        location ~* \.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot)$ {
            expires 1y;
            add_header Cache-Control "public, immutable";
        }
    }

    # Backend API proxy
    location /api/ {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
    }
}
```

**Automation**: Automatically executed in GitHub Actions (`.github/workflows/frontend.yml`)

---

## Monitoring

### Metrics to Monitor

- Page load time (FCP, LCP)
- API response time
- JavaScript error frequency
- User flow completion rate (signup → generation → payment)

### Tools

- **Google Analytics**: Page views, user behavior
- **Sentry**: JavaScript error tracking
- **Nginx logs**: Analyze Backend EC2's `/var/log/nginx/access.log`

---

## References

### Essential Documents
- **[CODE_GUIDE.md](CODE_GUIDE.md)** - Code writing patterns and examples (must read before coding)
- **[PLAN.md](PLAN.md)** - Development task plan (check next task)

### Project Documents
- **[TECHSPEC.md](../../TECHSPEC.md)** - Overall system architecture
- **[docs/API.md](../../docs/API.md)** - Backend API specification
- **[docs/PATTERNS.md](../../docs/PATTERNS.md)** - Common code patterns

### External Documentation
- **Vue 3**: https://vuejs.org/guide/introduction.html
- **Pinia**: https://pinia.vuejs.org/
- **Vue Router**: https://router.vuejs.org/
- **Tailwind CSS**: https://tailwindcss.com/docs
- **Vite**: https://vitejs.dev/guide/

---

## Troubleshooting

### Common Issues

**1. CORS error**
```bash
# Check Backend CORS configuration
# Verify CORS_ALLOWED_ORIGINS includes http://localhost:5173
```

**2. Session cookie not being sent**
```javascript
// Verify Axios configuration
axios.defaults.withCredentials = true
```

**3. Node version error**
```bash
# Check Node.js version (18+ required)
node -v

# If using nvm
nvm use 18
```

**4. Vite build error (out of memory)**
```bash
# Increase Node memory
export NODE_OPTIONS=--max-old-space-size=4096
npm run build
```

**5. E2E test failure**
```bash
# Install Playwright browsers
npx playwright install

# Disable headless mode
npm run test:e2e -- --headed
```

---

## Support

- **GitHub Issues**: Bug reports and feature requests
- **Team Communication**: Slack #frontend channel
- **Documentation**: [TECHSPEC.md](../../TECHSPEC.md)
