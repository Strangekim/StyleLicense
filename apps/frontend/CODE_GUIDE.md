# Frontend Code Guide

**Purpose**: Provides code patterns and examples to follow when developing Frontend based on Vue 3 + Pinia.

**Audience**: Frontend developers, Code reviewers

---

## Table of Contents

1. [Code Writing Principles](#1-code-writing-principles)
2. [Vue 3 Composition API](#2-vue-3-composition-api)
3. [Pinia Store Pattern](#3-pinia-store-pattern)
4. [Composable Pattern](#4-composable-pattern)
5. [Component Pattern](#5-component-pattern)
6. [API Communication](#6-api-communication)
7. [Infinite Scroll](#7-infinite-scroll)
8. [Error Handling](#8-error-handling)
9. [Performance Optimization](#9-performance-optimization)
10. [Testing](#10-testing)

---

## 1. Code Writing Principles

### 1.1 Vue 3 Philosophy

- **Use `<script setup>`** - Options API prohibited
- **Pinia Setup Store** - Options Store prohibited
- **Composition API** - Separate reusable logic into Composables
- **Feature-Sliced Design** - Folder structure by features

### 1.2 Naming Rules

```javascript
// File names
StyleCard.vue          // Component: PascalCase
useAuth.js             // Composable: use + camelCase
authStore.js           // Store: camelCase
authApi.js             // API: camelCase

// Variable names
const userName = ref('')              // camelCase
const isLoading = ref(false)          // Boolean: is/has/should prefix
const MAX_FILE_SIZE = 5 * 1024 * 1024 // Constants: UPPER_SNAKE_CASE
```

### 1.3 Import Order

```vue
<script setup>
// 1. Vue core
import { ref, computed, watch, onMounted } from 'vue'

// 2. Router / Pinia
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/features/auth/store/authStore'

// 3. Composables
import { useDebounce } from '@/shared/composables/useDebounce'

// 4. API
import { fetchStyles } from '@/features/styles/api/styleApi'

// 5. Components
import StyleCard from '@/features/styles/ui/StyleCard.vue'

// 6. Assets (Design resources)
import logo from '@/assets/images/main_logo.png'
import styleIcon from '@/assets/icons/style_icon.png'

// 7. Utils
import { validateEmail } from '@/shared/utils/validators'
</script>
```

**Design Asset Import**:
```vue
<script setup>
// Always import from src/assets/ (set up in vite.config.js)
import mainLogo from '@/assets/images/main_logo.png'
import mainLogoBlack from '@/assets/images/main_logo_black.png'
import brushIcon from '@/assets/icons/brush_icon.png'
import styleIcon from '@/assets/icons/style_icon.png'
import styleIconSelected from '@/assets/icons/style_icon_selected.png'
</script>

<template>
  <!-- Use :src binding for reactive images -->
  <img :src="mainLogo" alt="Style License" class="h-8" />
  <img :src="isActive ? styleIconSelected : styleIcon" alt="Styles" />
</template>
```

### 1.4 Feature-Sliced Design

```
src/features/auth/
├── ui/              # Vue components
├── api/             # API communication
├── store/           # Pinia Store
├── composables/     # Reusable logic
└── utils/           # Utilities
```

---

## 2. Vue 3 Composition API

### 2.1 Basic Structure

```vue
<script setup>
import { ref, computed, watch, onMounted } from 'vue'

// Props & Emits
const props = defineProps({
  userId: { type: String, required: true }
})
const emit = defineEmits(['update', 'delete'])

// State
const count = ref(0)
const user = ref(null)

// Computed
const doubleCount = computed(() => count.value * 2)

// Methods
function increment() {
  count.value++
  emit('update', count.value)
}

// Watch
watch(() => props.userId, (newId) => {
  fetchUserData(newId)
})

// Lifecycle
onMounted(() => {
  fetchUserData(props.userId)
})
</script>

<template>
  <div>
    <p>Count: {{ count }} (Double: {{ doubleCount }})</p>
    <button @click="increment">+1</button>
  </div>
</template>
```

### 2.2 Ref vs Reactive

```javascript
import { ref, reactive, toRefs } from 'vue'

// ✅ Ref: Suitable for primitive values
const count = ref(0)
const message = ref('Hello')
count.value++ // Access with .value

// ✅ Reactive: Entire object
const state = reactive({
  user: null,
  loading: false
})
state.loading = true // Direct access

// toRefs for Composable return
function useUser() {
  const state = reactive({ user: null, loading: false })
  return toRefs(state) // Destructurable
}
```

### 2.3 Computed vs Watch

```javascript
// ✅ Computed: Derived state (no side effects)
const fullName = computed(() => `${firstName.value} ${lastName.value}`)
const activeUsers = computed(() => users.value.filter(u => u.is_active))

// ✅ Watch: Side effects (API calls, localStorage, etc.)
watch(searchQuery, async (query) => {
  if (query.length > 2) {
    await searchStyles(query)
  }
})

// Watch multiple values
watch([firstName, lastName], ([newFirst, newLast]) => {
  console.log(`Name: ${newFirst} ${newLast}`)
})
```

---

## 3. Pinia Store Pattern

### 3.1 Setup Store (Recommended)

```javascript
// src/features/auth/store/authStore.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginUser, logoutUser } from '../api/authApi'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const isAuthenticated = computed(() => user.value !== null)
  const isArtist = computed(() => user.value?.role === 'artist')

  // Actions
  async function login(credentials) {
    loading.value = true
    error.value = null
    try {
      const response = await loginUser(credentials)
      user.value = response.data.user
      return true
    } catch (err) {
      error.value = err.response?.data?.message || 'Login failed'
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    await logoutUser()
    user.value = null
  }

  return { user, loading, error, isAuthenticated, isArtist, login, logout }
})
```

### 3.2 Using in Components

```vue
<script setup>
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/features/auth/store/authStore'

const authStore = useAuthStore()

// ✅ storeToRefs: Reactive destructuring of state/getters
const { user, isAuthenticated, loading } = storeToRefs(authStore)

// ✅ Actions: Direct destructuring
const { login, logout } = authStore
</script>

<template>
  <div v-if="isAuthenticated">
    <p>Welcome, {{ user.username }}!</p>
    <button @click="logout">Logout</button>
  </div>
</template>
```

### 3.3 Store Dependencies

```javascript
// src/features/tokens/store/tokenStore.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAuthStore } from '@/features/auth/store/authStore'

export const useTokenStore = defineStore('token', () => {
  const authStore = useAuthStore() // Reference another Store

  const balance = ref(0)

  const canGenerate = computed(() => {
    return authStore.isAuthenticated && balance.value >= 10
  })

  async function fetchBalance() {
    if (!authStore.isAuthenticated) return
    const response = await fetchTokenBalance()
    balance.value = response.data.balance
  }

  return { balance, canGenerate, fetchBalance }
})
```

---

## 4. Composable Pattern

### 4.1 useDebounce

```javascript
// src/shared/composables/useDebounce.js
import { ref, watch } from 'vue'

export function useDebounce(value, delay = 500) {
  const debouncedValue = ref(value.value)
  let timeout = null

  watch(value, (newValue) => {
    clearTimeout(timeout)
    timeout = setTimeout(() => {
      debouncedValue.value = newValue
    }, delay)
  })

  return debouncedValue
}
```

**Usage:**
```vue
<script setup>
import { ref, watch } from 'vue'
import { useDebounce } from '@/shared/composables/useDebounce'

const searchQuery = ref('')
const debouncedQuery = useDebounce(searchQuery, 500)

watch(debouncedQuery, async (query) => {
  if (query.length > 2) {
    await searchStyles(query)
  }
})
</script>
```

### 4.2 usePagination

```javascript
// src/shared/composables/usePagination.js
import { ref, computed } from 'vue'

export function usePagination(fetchFn, options = {}) {
  const { pageSize = 20 } = options

  const items = ref([])
  const currentPage = ref(1)
  const totalPages = ref(1)
  const loading = ref(false)

  const hasNextPage = computed(() => currentPage.value < totalPages.value)

  async function fetchPage(page) {
    loading.value = true
    try {
      const response = await fetchFn({ page, page_size: pageSize })
      items.value = response.data.results
      totalPages.value = Math.ceil(response.data.count / pageSize)
      currentPage.value = page
    } finally {
      loading.value = false
    }
  }

  async function nextPage() {
    if (hasNextPage.value) await fetchPage(currentPage.value + 1)
  }

  return { items, currentPage, totalPages, loading, hasNextPage, fetchPage, nextPage }
}
```

---

## 5. Component Pattern

### 5.0 Design Guidelines (IMPORTANT)

**Before implementing any component, review:**
- **Design mockups**: `docs/design/pages/` (17 PNG/JPG files)
- **Design System**: `README.md#design-system` (comprehensive guide)
- **TECHSPEC.md**: Authority for features (no comment likes, etc.)

**Key Principles**:
1. **Follow mockups with flexibility** - Adjust spacing/colors for consistency
2. **Instagram-inspired UI** - Reference Instagram for patterns
3. **Tailwind CSS** - Use utility classes, extract to tailwind.config.js
4. **Smooth animations** - 200-300ms transitions
5. **Accessibility** - ARIA labels, keyboard navigation, color contrast

**Example - Button Component**:
```vue
<!-- src/shared/ui/Button.vue -->
<script setup>
const props = defineProps({
  variant: { type: String, default: 'primary' }, // primary, secondary, outline
  size: { type: String, default: 'md' }, // sm, md, lg
  loading: { type: Boolean, default: false }
})
</script>

<template>
  <!-- Base classes + variant classes + smooth transition -->
  <button
    :class="[
      'rounded-lg font-medium transition-colors duration-200',
      'focus:outline-none focus:ring-2 focus:ring-offset-2',
      {
        'bg-blue-600 text-white hover:bg-blue-700 focus:ring-blue-500': variant === 'primary',
        'bg-gray-200 text-gray-800 hover:bg-gray-300 focus:ring-gray-400': variant === 'secondary',
        'border-2 border-blue-600 text-blue-600 hover:bg-blue-50': variant === 'outline',
        'px-3 py-1.5 text-sm': size === 'sm',
        'px-4 py-2 text-base': size === 'md',
        'px-6 py-3 text-lg': size === 'lg',
        'opacity-50 cursor-not-allowed': loading
      }
    ]"
    :disabled="loading"
  >
    <!-- Loading spinner (Instagram-style) -->
    <svg v-if="loading" class="animate-spin h-5 w-5 inline-block mr-2" viewBox="0 0 24 24">
      <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" fill="none"/>
      <path class="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"/>
    </svg>
    <slot />
  </button>
</template>
```

**Extract to Tailwind Config**:
```javascript
// tailwind.config.js - Extract common colors/values
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50: '#eff6ff',
          500: '#3b82f6',  // From mockups
          600: '#2563eb',
          700: '#1d4ed8'
        }
      },
      transitionDuration: {
        '200': '200ms',  // Standard transition
      }
    }
  }
}
```

**Component Checklist**:
- [ ] Matches mockup design (or Instagram pattern)
- [ ] TECHSPEC.md features only (no extras)
- [ ] Smooth transitions (200-300ms)
- [ ] Mobile responsive
- [ ] Loading/error/empty states
- [ ] Accessible (ARIA, keyboard nav)

---

### 5.1 Smart vs Presentational

**Smart (Contains logic):**
```vue
<!-- src/features/styles/ui/StyleGrid.vue -->
<script setup>
import { onMounted } from 'vue'
import { useStyleStore } from '@/features/styles/store/styleStore'
import { storeToRefs } from 'pinia'
import StyleCard from './StyleCard.vue'

const styleStore = useStyleStore()
const { styles, loading } = storeToRefs(styleStore)

onMounted(() => styleStore.fetchStyles())

function handleClick(styleId) {
  styleStore.selectStyle(styleId)
}
</script>

<template>
  <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
    <StyleCard
      v-for="style in styles"
      :key="style.id"
      :style="style"
      @click="handleClick(style.id)"
    />
  </div>
</template>
```

**Presentational (Pure UI):**
```vue
<!-- src/features/styles/ui/StyleCard.vue -->
<script setup>
const props = defineProps({
  style: { type: Object, required: true }
})
const emit = defineEmits(['click'])
</script>

<template>
  <div class="rounded-lg shadow-md cursor-pointer hover:-translate-y-1 transition"
       @click="emit('click')">
    <img :src="style.thumbnail_url" :alt="style.name" class="w-full" />
    <div class="p-4">
      <h3 class="font-bold">{{ style.name }}</h3>
      <p class="text-sm text-gray-600">{{ style.artist_name }}</p>
      <div class="flex justify-between mt-2">
        <span>{{ style.generation_cost_tokens }} tokens</span>
        <span>❤️ {{ style.like_count }}</span>
      </div>
    </div>
  </div>
</template>
```

### 5.2 Form Validation (Zod)

```vue
<script setup>
import { ref, computed } from 'vue'
import { z } from 'zod'
import { useAuthStore } from '@/features/auth/store/authStore'

const loginSchema = z.object({
  email: z.string().email('Invalid email format'),
  password: z.string().min(8, 'Password must be at least 8 characters')
})

const email = ref('')
const password = ref('')
const errors = ref({})

function validateField(field, value) {
  try {
    loginSchema.shape[field].parse(value)
    delete errors.value[field]
  } catch (err) {
    errors.value[field] = err.errors[0].message
  }
}

async function handleSubmit() {
  try {
    loginSchema.parse({ email: email.value, password: password.value })
    errors.value = {}
    await useAuthStore().login({ email: email.value, password: password.value })
  } catch (err) {
    if (err instanceof z.ZodError) {
      errors.value = err.flatten().fieldErrors
    }
  }
}
</script>

<template>
  <form @submit.prevent="handleSubmit">
    <div>
      <input v-model="email" @blur="validateField('email', email)" />
      <span v-if="errors.email" class="text-red-500 text-sm">{{ errors.email }}</span>
    </div>
    <button type="submit">Login</button>
  </form>
</template>
```

---

## 6. API Communication

### 6.1 Axios Instance

```javascript
// src/shared/api/axios.js
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 10000,
  withCredentials: true, // Session cookie
  headers: { 'Content-Type': 'application/json' }
})

// Response Interceptor
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      window.location.href = '/login'
    }
    return Promise.reject(error)
  }
)

export default api
```

### 6.2 API Functions

```javascript
// src/features/styles/api/styleApi.js
import api from '@/shared/api/axios'

export async function fetchStyles(params = {}) {
  return api.get('/styles', { params })
}

export async function fetchStyleById(styleId) {
  return api.get(`/styles/${styleId}`)
}

export async function createStyle(formData) {
  return api.post('/styles', formData, {
    headers: { 'Content-Type': 'multipart/form-data' }
  })
}

export async function searchStyles(query) {
  return api.get('/search', { params: { type: 'styles', q: query } })
}
```

### 6.3 File Upload

```javascript
export async function uploadStyleImages(files, metadata) {
  const formData = new FormData()
  files.forEach(file => formData.append('images', file))
  formData.append('name', metadata.name)
  formData.append('description', metadata.description)

  return api.post('/styles', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (e) => {
      console.log(`${Math.round((e.loaded * 100) / e.total)}%`)
    }
  })
}
```

### 6.4 Polling (Training Progress)

```javascript
// src/features/styles/composables/useTrainingProgress.js
import { ref, onUnmounted } from 'vue'
import { fetchStyleById } from '../api/styleApi'

export function useTrainingProgress(styleId) {
  const progress = ref(0)
  const status = ref('pending')
  let pollInterval = null

  async function checkProgress() {
    const response = await fetchStyleById(styleId)
    progress.value = response.data.training_progress || 0
    status.value = response.data.status

    if (status.value === 'completed' || status.value === 'failed') {
      stopPolling()
    }
  }

  function startPolling(interval = 3000) {
    checkProgress()
    pollInterval = setInterval(checkProgress, interval)
  }

  function stopPolling() {
    if (pollInterval) clearInterval(pollInterval)
  }

  onUnmounted(() => stopPolling())

  return { progress, status, startPolling, stopPolling }
}
```

---

## 7. Infinite Scroll

### 7.1 useInfiniteScroll

```javascript
// src/shared/composables/useInfiniteScroll.js
import { ref, computed, onUnmounted } from 'vue'

export function useInfiniteScroll(fetchFn, options = {}) {
  const { pageSize = 20, threshold = 0.5 } = options

  const items = ref([])
  const cursor = ref(null)
  const loading = ref(false)
  const hasMore = ref(true)
  const observerTarget = ref(null)

  let observer = null

  async function loadMore() {
    if (loading.value || !hasMore.value) return

    loading.value = true
    try {
      const response = await fetchFn({ cursor: cursor.value, page_size: pageSize })
      items.value = [...items.value, ...response.data.results]
      cursor.value = response.data.next_cursor
      hasMore.value = response.data.has_next
    } finally {
      loading.value = false
    }
  }

  function setupObserver() {
    if (!observerTarget.value) return
    observer = new IntersectionObserver(
      (entries) => {
        if (entries[0].isIntersecting) loadMore()
      },
      { threshold }
    )
    observer.observe(observerTarget.value)
  }

  function reset() {
    items.value = []
    cursor.value = null
    hasMore.value = true
  }

  onUnmounted(() => observer?.disconnect())

  return { items, loading, hasMore, observerTarget, loadMore, setupObserver, reset }
}
```

### 7.2 Usage Example

```vue
<script setup>
import { onMounted } from 'vue'
import { useInfiniteScroll } from '@/shared/composables/useInfiniteScroll'
import { fetchGenerations } from '@/features/generations/api/generationApi'

const {
  items: generations,
  loading,
  hasMore,
  observerTarget,
  loadMore,
  setupObserver
} = useInfiniteScroll(fetchGenerations, { pageSize: 20 })

onMounted(async () => {
  await loadMore()
  setupObserver()
})
</script>

<template>
  <div>
    <div class="grid grid-cols-3 gap-4">
      <GenerationCard v-for="gen in generations" :key="gen.id" :generation="gen" />
    </div>

    <!-- Observer target -->
    <div ref="observerTarget" class="h-24 flex items-center justify-center">
      <LoadingSpinner v-if="loading" />
      <p v-else-if="!hasMore">All posts loaded</p>
    </div>
  </div>
</template>
```

---

## 8. Error Handling

### 8.1 Toast Composable

```javascript
// src/shared/composables/useToast.js
import { ref } from 'vue'

const toasts = ref([])
let idCounter = 0

export function useToast() {
  function showToast(message, type = 'info', duration = 3000) {
    const id = idCounter++
    toasts.value.push({ id, message, type })
    if (duration > 0) {
      setTimeout(() => removeToast(id), duration)
    }
  }

  function removeToast(id) {
    const index = toasts.value.findIndex(t => t.id === id)
    if (index > -1) toasts.value.splice(index, 1)
  }

  return {
    toasts,
    success: (msg, dur) => showToast(msg, 'success', dur),
    error: (msg, dur) => showToast(msg, 'error', dur),
    warning: (msg, dur) => showToast(msg, 'warning', dur),
    removeToast
  }
}
```

### 8.2 Toast Component

```vue
<!-- src/shared/ui/ToastContainer.vue -->
<script setup>
import { useToast } from '@/shared/composables/useToast'
const { toasts, removeToast } = useToast()
</script>

<template>
  <div class="fixed top-4 right-4 z-50">
    <div
      v-for="toast in toasts"
      :key="toast.id"
      @click="removeToast(toast.id)"
      :class="[
        'mb-2 p-4 rounded-lg shadow-lg cursor-pointer animate-slide-in',
        toast.type === 'success' && 'bg-green-500 text-white',
        toast.type === 'error' && 'bg-red-500 text-white',
        toast.type === 'warning' && 'bg-yellow-500 text-white'
      ]"
    >
      {{ toast.message }}
    </div>
  </div>
</template>
```

### 8.3 Form Error Handling

```vue
<script setup>
import { ref } from 'vue'
import { z } from 'zod'
import { useToast } from '@/shared/composables/useToast'
import { createStyle } from '@/features/styles/api/styleApi'

const toast = useToast()
const formData = ref({ name: '', description: '' })
const errors = ref({})

const schema = z.object({
  name: z.string().min(2, 'Name must be at least 2 characters').max(50),
  description: z.string().max(500)
})

async function handleSubmit() {
  try {
    schema.parse(formData.value)
    errors.value = {}
    await createStyle(formData.value)
    toast.success('Created successfully!')
  } catch (err) {
    if (err instanceof z.ZodError) {
      errors.value = err.flatten().fieldErrors
      toast.error('Please check your input')
    } else if (err.response?.status === 400) {
      errors.value = err.response.data.errors || {}
      toast.error(err.response.data.message)
    }
  }
}
</script>
```

---

## 9. Performance Optimization

### 9.1 Component Lazy Loading

```javascript
// src/router/index.js
const routes = [
  {
    path: '/',
    component: () => import('@/pages/HomePage.vue') // Lazy
  },
  {
    path: '/styles/:id',
    component: () => import('@/features/styles/ui/StyleDetailPage.vue')
  }
]
```

### 9.2 Image Lazy Loading

```vue
<script setup>
import { ref, onMounted } from 'vue'

const props = defineProps({ src: String })
const imgRef = ref(null)
const loaded = ref(false)

onMounted(() => {
  const observer = new IntersectionObserver((entries) => {
    if (entries[0].isIntersecting) {
      loaded.value = true
      observer.disconnect()
    }
  })
  if (imgRef.value) observer.observe(imgRef.value)
})
</script>

<template>
  <img ref="imgRef" :src="loaded ? src : '/placeholder.jpg'" />
</template>
```

### 9.3 Computed vs Watch

```javascript
// ✅ Computed: Derived state
const filteredStyles = computed(() =>
  styles.value.filter(s => s.name.includes(searchQuery.value))
)

// ✅ Watch: Side effects
watch(userId, async (id) => {
  user.value = await fetchUserData(id)
})

// ❌ Watch for derived state (inefficient)
watch([styles, searchQuery], () => {
  filteredStyles.value = styles.value.filter(...)
})
```

### 9.4 Virtual Scrolling (Large Datasets)

```vue
<script setup>
import { RecycleScroller } from 'vue-virtual-scroller'
import 'vue-virtual-scroller/dist/vue-virtual-scroller.css'

const items = ref([]) // 1000+ items
</script>

<template>
  <RecycleScroller :items="items" :item-size="200" key-field="id" v-slot="{ item }">
    <StyleCard :style="item" />
  </RecycleScroller>
</template>
```

---

## 10. Testing

### 10.1 Composable Testing

```javascript
// src/shared/composables/useDebounce.test.js
import { describe, it, expect, vi } from 'vitest'
import { ref } from 'vue'
import { useDebounce } from './useDebounce'

describe('useDebounce', () => {
  it('should debounce value', async () => {
    vi.useFakeTimers()

    const value = ref('initial')
    const debouncedValue = useDebounce(value, 500)

    value.value = 'new'
    expect(debouncedValue.value).toBe('initial')

    vi.advanceTimersByTime(500)
    expect(debouncedValue.value).toBe('new')

    vi.useRealTimers()
  })
})
```

### 10.2 Component Testing

```javascript
// src/features/styles/ui/StyleCard.test.js
import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import StyleCard from './StyleCard.vue'

describe('StyleCard', () => {
  const mockStyle = {
    id: 1,
    name: 'Test Style',
    artist_name: 'Artist',
    thumbnail_url: 'https://example.com/img.jpg',
    generation_cost_tokens: 10
  }

  it('renders correctly', () => {
    const wrapper = mount(StyleCard, { props: { style: mockStyle } })
    expect(wrapper.text()).toContain('Test Style')
    expect(wrapper.text()).toContain('10 tokens')
  })

  it('emits click event', async () => {
    const wrapper = mount(StyleCard, { props: { style: mockStyle } })
    await wrapper.trigger('click')
    expect(wrapper.emitted()).toHaveProperty('click')
  })
})
```

### 10.3 Store Testing

```javascript
// src/features/auth/store/authStore.test.js
import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useAuthStore } from './authStore'
import * as authApi from '../api/authApi'

vi.mock('../api/authApi')

describe('useAuthStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('should login successfully', async () => {
    const authStore = useAuthStore()
    authApi.loginUser.mockResolvedValue({
      data: { user: { id: 1, username: 'test' } }
    })

    const result = await authStore.login({ email: 'test@example.com', password: 'pass' })

    expect(result).toBe(true)
    expect(authStore.isAuthenticated).toBe(true)
  })
})
```

---

## Reference Documents

- **[Frontend README.md](README.md)** - Project structure and environment
- **[docs/API.md](../../docs/API.md)** - Backend API specification
- **[docs/PATTERNS.md](../../docs/PATTERNS.md)** - Common patterns

---

## Checklist

**Before writing code:**
- [ ] Read Frontend README.md
- [ ] Check docs/API.md
- [ ] Check this CODE_GUIDE.md patterns

**When writing code:**
- [ ] Use `<script setup>`
- [ ] Pinia Setup Store pattern
- [ ] Feature-Sliced Design structure
- [ ] Zod form validation
- [ ] try-catch error handling
- [ ] Use Tailwind CSS

**After writing code:**
- [ ] Pass `npm run lint`
- [ ] Run `npm run format`
- [ ] Pass `npm run test`
- [ ] Verify browser functionality
