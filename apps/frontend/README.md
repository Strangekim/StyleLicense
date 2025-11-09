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

## Design System

### Overview

Style License frontend follows design mockups located in `docs/design/pages/` with Instagram-inspired UI patterns. All design resources (logos, icons, page mockups) are integrated into the development workflow.

**Design Philosophy**:
- **Instagram-inspired**: Modern, clean, mobile-first design language
- **Consistency over exactness**: Maintain visual consistency across all pages (colors, fonts, spacing)
- **Commercial standards**: Follow industry best practices for UX/UI

---

### Design Resources Location

```
Project structure:
docs/design/
└── pages/                    # 17 page design mockups (PNG/JPG)
    ├── LogIn Page.png
    ├── Main Page.png
    ├── Feed detail Page1-2.png
    ├── Search & Following Artist Page.png
    ├── StyleDetailPage1-4.png
    ├── Create Style Page1-3.png
    ├── Profile Page.png
    ├── Edit Profile1-2.png
    ├── Notification Page.png
    └── Comment Modal.jpg

apps/frontend/src/assets/
├── images/                   # Production logos
│   ├── main_logo.png        # Primary logo (light bg)
│   ├── main_logo_black.png  # Logo variant (dark bg)
│   ├── main_typo.png        # Typography/wordmark
│   └── styleLicense_logo.png # Alternative logo
└── icons/                    # Production icons
    ├── brush_icon.png       # Art/style actions
    ├── style_icon.png       # Navigation (inactive)
    └── style_icon_selected.png # Navigation (active)
```

---

### UI Design Guidelines

#### 1. Follow Page Mockups with Flexibility

**Base Reference**: Always start with mockups in `docs/design/pages/`

**Allowed Adjustments**:
- ✅ Adjust component spacing for better visual hierarchy
- ✅ Unify font sizes across similar elements
- ✅ Standardize colors for consistency (e.g., all primary buttons same color)
- ✅ Improve alignment and grid consistency
- ✅ Enhance responsive behavior for mobile/tablet

**Example**:
```vue
<!-- Mockup shows 12px gap, but 16px provides better breathing room -->
<div class="flex flex-col gap-4">  <!-- gap-4 = 16px, not 12px -->
  <Button />
  <Input />
</div>
```

#### 2. Instagram UI Patterns

Use Instagram as the primary reference for:
- **Feed layouts**: Grid/masonry for image galleries
- **Navigation**: Bottom tab bar (mobile), sidebar (desktop)
- **Modals**: Comment modal, share modal, settings modal
- **Interactions**: Like button animation, follow button states
- **Loading states**: Skeleton loaders, shimmer effects

**Instagram Reference**:
- https://www.instagram.com/ (web version)
- Focus on: Feed, Profile, Explore pages

#### 3. Handle Missing Specifications

When page mockups don't cover specific features:
- **Option 1**: Reference Instagram's implementation
- **Option 2**: Follow modern design trends (e.g., Dribbble, Behance)
- **Option 3**: Use industry standards (Material Design, Apple HIG)

**Examples**:
- **Loading state**: No mockup? → Use skeleton loader (Instagram-style)
- **Error state**: No mockup? → Use toast notification (common pattern)
- **Empty state**: No mockup? → Centered icon + text + action button

#### 4. TECHSPEC.md Authority (Critical)

**If mockup conflicts with TECHSPEC.md requirements, TECHSPEC.md wins.**

**Excluded Features** (present in mockups but NOT in TECHSPEC.md):
- ❌ **Comment likes** - Comment Modal.jpg shows like button on comments, but TECHSPEC.md line 751 explicitly states "댓글 좋아요 없음"
- ❌ Any feature not listed in TECHSPEC.md sections 6-8

**Verification Process**:
1. Check mockup design
2. Cross-reference with TECHSPEC.md
3. If feature is missing from TECHSPEC.md → **Do NOT implement**
4. If uncertain → Ask for clarification

**Example**:
```vue
<!-- ❌ WRONG: Comment like button (not in TECHSPEC.md) -->
<button @click="likeComment">
  <HeartIcon />
</button>

<!-- ✅ CORRECT: Only show comments, no like interaction -->
<div class="comment">
  <p>{{ comment.content }}</p>
</div>
```

#### 5. Commercial Standards

All UI interactions must follow industry best practices:
- **Smooth animations**: 200-300ms transitions (not instant, not slow)
- **Clear feedback**: Loading states, success/error messages
- **Accessible**: ARIA labels, keyboard navigation, color contrast
- **Responsive**: Mobile-first design, breakpoints at 640px, 768px, 1024px
- **Performance**: Lazy loading images, virtualized lists

**Example**:
```vue
<!-- ✅ GOOD: Clear loading state, smooth transition -->
<button
  @click="handleSubmit"
  :disabled="isLoading"
  class="transition-colors duration-200 hover:bg-blue-600"
>
  <SpinnerIcon v-if="isLoading" class="animate-spin" />
  <span v-else>Submit</span>
</button>
```

---

### Asset Usage

#### Using Logos in Components

```vue
<script setup>
import mainLogo from '@/assets/images/main_logo.png'
import mainLogoBlack from '@/assets/images/main_logo_black.png'
import mainTypo from '@/assets/images/main_typo.png'
</script>

<template>
  <!-- Header logo -->
  <img :src="mainLogo" alt="Style License" class="h-8" />

  <!-- Dark mode logo -->
  <img v-if="isDarkMode" :src="mainLogoBlack" alt="Style License" />

  <!-- Typography only (e.g., footer) -->
  <img :src="mainTypo" alt="Style License" class="h-6" />
</template>
```

#### Using Icons in Components

```vue
<script setup>
import { ref } from 'vue'
import styleIcon from '@/assets/icons/style_icon.png'
import styleIconSelected from '@/assets/icons/style_icon_selected.png'
import brushIcon from '@/assets/icons/brush_icon.png'

const isActive = ref(false)
</script>

<template>
  <!-- Navigation icon (bottom tab bar) -->
  <button @click="navigate">
    <img
      :src="isActive ? styleIconSelected : styleIcon"
      alt="Styles"
      class="w-6 h-6"
    />
  </button>

  <!-- Action button icon -->
  <button>
    <img :src="brushIcon" alt="Create" class="w-5 h-5" />
  </button>
</template>
```

---

### Page Mockup Reference

Map each page component to its design mockup:

| Page Component | Mockup Reference | Key Features |
|----------------|------------------|--------------|
| **LoginPage.vue** | `LogIn Page.png` | Google OAuth button, logo, tagline |
| **MainPage.vue** | `Main Page.png` | Feed grid, infinite scroll, bottom nav |
| **FeedDetailPage.vue** | `Feed detail Page1.png`, `Feed detail Page2.png` | Image detail, comments, like button |
| **SearchPage.vue** | `Search & Following Artist Page.png` | Search bar, following section, results grid |
| **StyleDetailPage.vue** | `StyleDetailPage1-4.png` | Style info, sample gallery, generation form |
| **EditStylePage.vue** | `Create Style Page1-3.png` | Image upload, tag input, training progress |
| **MyPage.vue** | `Profile Page.png` | User profile, portfolio grid, edit button |
| **EditProfilePage.vue** | `Edit Profile1-2.png` | Profile form, image upload |
| **NotificationPage.vue** | `Notification Page.png` | Notification list, mark as read |
| **Comment Modal** | `Comment Modal.jpg` | Modal overlay, comment list, input |

**Usage**:
1. Open mockup from `docs/design/pages/`
2. Analyze layout, colors, spacing, components
3. Implement with Tailwind CSS + Vue 3 Composition API
4. Adjust for consistency (spacing, colors, fonts)

---

### Design System Setup

#### Color Extraction (TODO)

Extract colors from mockups and define in `tailwind.config.js`:

```javascript
// apps/frontend/tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#...',   // Extract from mockups
          500: '#...',  // Main brand color
          900: '#...',
        },
        secondary: { /* ... */ },
        neutral: { /* ... */ },
        success: '#...',
        error: '#...',
        warning: '#...',
      }
    }
  }
}
```

#### Typography (TODO)

Identify font families and sizes from mockups:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],  // Primary font
        display: ['...'],  // Headings (if different)
      },
      fontSize: {
        'xs': '0.75rem',   // 12px
        'sm': '0.875rem',  // 14px
        'base': '1rem',    // 16px
        'lg': '1.125rem',  // 18px
        'xl': '1.25rem',   // 20px
        '2xl': '1.5rem',   // 24px
        // ... adjust based on mockups
      }
    }
  }
}
```

#### Spacing & Layout

Define consistent spacing scale:

```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      spacing: {
        '18': '4.5rem',   // Custom spacing if needed
        '88': '22rem',
      },
      borderRadius: {
        'xl': '1rem',     // Card corners
        '2xl': '1.5rem',  // Modal corners
      },
      maxWidth: {
        'screen-xl': '1280px',  // Container max width
      }
    }
  }
}
```

---

### Implementation Workflow

When implementing a new page:

1. **Reference mockup**: Open corresponding PNG from `docs/design/pages/`
2. **Extract specs**: Note colors, spacing, font sizes, component structure
3. **Check TECHSPEC.md**: Verify all features are required (remove if not listed)
4. **Implement structure**: Create layout with Tailwind classes
5. **Add interactions**: Follow Instagram patterns for hover/click states
6. **Test responsiveness**: Ensure mobile/tablet/desktop views work
7. **Refine consistency**: Adjust spacing/colors if inconsistent with other pages

**Example checklist for MainPage.vue**:
- [ ] Extract color palette from Main Page.png
- [ ] Implement grid layout (Instagram-style)
- [ ] Add infinite scroll (useInfiniteScroll composable)
- [ ] Verify feed API matches TECHSPEC.md GET /api/generations/feed
- [ ] Add loading skeleton (Instagram-style shimmer)
- [ ] Test mobile responsiveness
- [ ] Add smooth transitions (200ms)

---

### Design System Maintenance

**Consistency Checks**:
- [ ] All buttons use same primary color
- [ ] All cards have consistent border radius
- [ ] All text uses defined font scale
- [ ] All spacing follows 4px/8px grid
- [ ] All interactive elements have hover/focus states
- [ ] All forms have validation states (error, success)

**Tools**:
- **Figma** (if available): Export design tokens automatically
- **Color Picker**: Extract exact hex codes from mockups
- **Design Linter**: Check for inconsistencies (manual review)

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
# Backend API URL for local development
VITE_API_BASE_URL=http://localhost:8000

# Production API URL (will be proxied by the frontend host or configured directly)
VITE_PROD_API_BASE_URL=https://api.stylelicense.com

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

## Deployment (GCP)

### Production Deployment to Cloud Storage + CDN

이 Vue.js 프론트엔드 애플리케이션은 정적 웹사이트로 빌드되어 **Google Cloud Storage**에 호스팅되고, **Google Cloud CDN**을 통해 전 세계 사용자에게 빠르고 안전하게(HTTPS) 제공됩니다.

### Deployment Steps

1.  **Production Build**:
    로컬 또는 CI/CD 환경에서 프로덕션용 정적 파일을 빌드합니다. 빌드 결과물은 `dist` 폴더에 생성됩니다.
    ```bash
    npm run build
    ```

2.  **Upload to Google Cloud Storage**:
    `gcloud` CLI를 사용하여 `dist` 폴더의 모든 내용을 Cloud Storage 버킷에 업로드합니다. `-r` 플래그는 디렉토리를 재귀적으로 복사합니다.
    ```bash
    # -m 플래그는 병렬 업로드를 활성화하여 속도를 높입니다.
    gcloud storage cp -r dist/* gs://your-frontend-bucket -m
    ```

3.  **Set Public Access**:
    업로드된 파일들을 웹에서 접근할 수 있도록 버킷의 모든 객체에 공개 읽기 권한을 부여합니다.
    ```bash
    gcloud storage buckets add-iam-policy-binding gs://your-frontend-bucket --member=allUsers --role=roles/storage.objectViewer
    ```

4.  **Configure as a Website**:
    버킷을 웹사이트로 작동하도록 설정하고, SPA(Single Page Application) 라우팅을 위해 에러 페이지를 `index.html`로 지정합니다.
    ```bash
    gcloud storage buckets update gs://your-frontend-bucket --web-main-page-suffix=index.html --web-error-page=index.html
    ```

5.  **Setup Cloud CDN and HTTPS**:
    - GCP 콘솔에서 `Cloud CDN`을 설정하고, 백엔드로 Cloud Storage 버킷을 지정합니다.
    - 이 과정을 통해 생성된 로드밸런서에 Google 관리 SSL 인증서가 자동으로 발급 및 적용되어 커스텀 도메인(예: `www.stylelicense.com`)에 대한 HTTPS가 활성화됩니다.

### Automation
이 모든 과정은 GitHub Actions와 같은 CI/CD 파이프라인을 통해 자동화하는 것이 권장됩니다. `main` 브랜치에 코드가 머지되면, 빌드, 테스트, GCS 업로드 과정이 자동으로 실행됩니다.

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
- **Design System** (above) - UI design guidelines, mockups, and asset usage

### Project Documents
- **[TECHSPEC.md](../../TECHSPEC.md)** - Overall system architecture (authority for features)
- **[docs/API.md](../../docs/API.md)** - Backend API specification
- **[docs/PATTERNS.md](../../docs/PATTERNS.md)** - Common code patterns
- **[docs/design/pages/](../../docs/design/pages/)** - Page design mockups (17 screens)

### Design References
- **Instagram Web**: https://www.instagram.com/ - Primary UI pattern reference
- **Tailwind CSS**: https://tailwindcss.com/docs - Styling framework
- **Dribbble**: https://dribbble.com/ - Design inspiration
- **Material Design**: https://m3.material.io/ - Component patterns

### External Documentation
- **Vue 3**: https://vuejs.org/guide/introduction.html
- **Pinia**: https://pinia.vuejs.org/
- **Vue Router**: https://router.vuejs.org/
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
