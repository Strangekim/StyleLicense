# Frontend Code Guide

**목적**: Vue 3 + Pinia 기반 Frontend 개발 시 따라야 할 코드 패턴과 예제를 제공합니다.

**대상**: Frontend 개발자, 코드 리뷰어

---

## 목차

1. [코드 작성 원칙](#1-코드-작성-원칙)
2. [Vue 3 Composition API](#2-vue-3-composition-api)
3. [Pinia Store 패턴](#3-pinia-store-패턴)
4. [Composable 패턴](#4-composable-패턴)
5. [컴포넌트 패턴](#5-컴포넌트-패턴)
6. [API 통신](#6-api-통신)
7. [무한 스크롤](#7-무한-스크롤)
8. [에러 핸들링](#8-에러-핸들링)
9. [성능 최적화](#9-성능-최적화)
10. [테스트](#10-테스트)

---

## 1. 코드 작성 원칙

### 1.1 Vue 3 철학

- **`<script setup>` 사용** - Options API 금지
- **Pinia Setup Store** - Options Store 금지
- **Composition API** - 재사용 가능한 로직은 Composable로 분리
- **Feature-Sliced Design** - 기능별 폴더 구조

### 1.2 네이밍 규칙

```javascript
// 파일명
StyleCard.vue          // 컴포넌트: PascalCase
useAuth.js             // Composable: use + camelCase
authStore.js           // Store: camelCase
authApi.js             // API: camelCase

// 변수명
const userName = ref('')              // camelCase
const isLoading = ref(false)          // Boolean: is/has/should prefix
const MAX_FILE_SIZE = 5 * 1024 * 1024 // 상수: UPPER_SNAKE_CASE
```

### 1.3 Import 순서

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

// 6. Utils
import { validateEmail } from '@/shared/utils/validators'
</script>
```

### 1.4 Feature-Sliced Design

```
src/features/auth/
├── ui/              # Vue 컴포넌트
├── api/             # API 통신
├── store/           # Pinia Store
├── composables/     # 재사용 로직
└── utils/           # 유틸리티
```

---

## 2. Vue 3 Composition API

### 2.1 기본 구조

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

// ✅ Ref: 원시값에 적합
const count = ref(0)
const message = ref('Hello')
count.value++ // .value로 접근

// ✅ Reactive: 객체 전체
const state = reactive({
  user: null,
  loading: false
})
state.loading = true // 직접 접근

// Composable 반환 시 toRefs
function useUser() {
  const state = reactive({ user: null, loading: false })
  return toRefs(state) // 구조 분해 가능
}
```

### 2.3 Computed vs Watch

```javascript
// ✅ Computed: 파생 상태 (side effect 없음)
const fullName = computed(() => `${firstName.value} ${lastName.value}`)
const activeUsers = computed(() => users.value.filter(u => u.is_active))

// ✅ Watch: Side effect (API 호출, localStorage 등)
watch(searchQuery, async (query) => {
  if (query.length > 2) {
    await searchStyles(query)
  }
})

// 여러 값 감시
watch([firstName, lastName], ([newFirst, newLast]) => {
  console.log(`Name: ${newFirst} ${newLast}`)
})
```

---

## 3. Pinia Store 패턴

### 3.1 Setup Store (권장)

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
      error.value = err.response?.data?.message || '로그인 실패'
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

### 3.2 컴포넌트에서 사용

```vue
<script setup>
import { storeToRefs } from 'pinia'
import { useAuthStore } from '@/features/auth/store/authStore'

const authStore = useAuthStore()

// ✅ storeToRefs: state/getters 반응형 구조 분해
const { user, isAuthenticated, loading } = storeToRefs(authStore)

// ✅ Actions: 직접 구조 분해
const { login, logout } = authStore
</script>

<template>
  <div v-if="isAuthenticated">
    <p>환영합니다, {{ user.username }}님!</p>
    <button @click="logout">로그아웃</button>
  </div>
</template>
```

### 3.3 Store 간 의존성

```javascript
// src/features/tokens/store/tokenStore.js
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useAuthStore } from '@/features/auth/store/authStore'

export const useTokenStore = defineStore('token', () => {
  const authStore = useAuthStore() // 다른 Store 참조

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

## 4. Composable 패턴

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

**사용:**
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

## 5. 컴포넌트 패턴

### 5.1 Smart vs Presentational

**Smart (로직 포함):**
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

**Presentational (순수 UI):**
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
        <span>{{ style.generation_cost_tokens }} 토큰</span>
        <span>❤️ {{ style.like_count }}</span>
      </div>
    </div>
  </div>
</template>
```

### 5.2 Form 검증 (Zod)

```vue
<script setup>
import { ref, computed } from 'vue'
import { z } from 'zod'
import { useAuthStore } from '@/features/auth/store/authStore'

const loginSchema = z.object({
  email: z.string().email('올바른 이메일 형식이 아닙니다'),
  password: z.string().min(8, '비밀번호는 최소 8자 이상')
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
    <button type="submit">로그인</button>
  </form>
</template>
```

---

## 6. API 통신

### 6.1 Axios 인스턴스

```javascript
// src/shared/api/axios.js
import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000/api',
  timeout: 10000,
  withCredentials: true, // 세션 쿠키
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

### 6.2 API 함수

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

### 6.3 파일 업로드

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

### 6.4 폴링 (학습 진행률)

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

## 7. 무한 스크롤

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

### 7.2 사용 예제

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

    <!-- Observer 타겟 -->
    <div ref="observerTarget" class="h-24 flex items-center justify-center">
      <LoadingSpinner v-if="loading" />
      <p v-else-if="!hasMore">모든 게시물을 불러왔습니다</p>
    </div>
  </div>
</template>
```

---

## 8. 에러 핸들링

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

### 8.2 Toast 컴포넌트

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

### 8.3 Form 에러 처리

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
  name: z.string().min(2, '이름은 최소 2자').max(50),
  description: z.string().max(500)
})

async function handleSubmit() {
  try {
    schema.parse(formData.value)
    errors.value = {}
    await createStyle(formData.value)
    toast.success('생성 완료!')
  } catch (err) {
    if (err instanceof z.ZodError) {
      errors.value = err.flatten().fieldErrors
      toast.error('입력값을 확인하세요')
    } else if (err.response?.status === 400) {
      errors.value = err.response.data.errors || {}
      toast.error(err.response.data.message)
    }
  }
}
</script>
```

---

## 9. 성능 최적화

### 9.1 컴포넌트 Lazy Loading

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

### 9.2 이미지 Lazy Loading

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
// ✅ Computed: 파생 상태
const filteredStyles = computed(() =>
  styles.value.filter(s => s.name.includes(searchQuery.value))
)

// ✅ Watch: Side effect
watch(userId, async (id) => {
  user.value = await fetchUserData(id)
})

// ❌ Watch로 파생 상태 (비효율)
watch([styles, searchQuery], () => {
  filteredStyles.value = styles.value.filter(...)
})
```

### 9.4 Virtual Scrolling (대량 데이터)

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

## 10. 테스트

### 10.1 Composable 테스트

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

### 10.2 컴포넌트 테스트

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
    expect(wrapper.text()).toContain('10 토큰')
  })

  it('emits click event', async () => {
    const wrapper = mount(StyleCard, { props: { style: mockStyle } })
    await wrapper.trigger('click')
    expect(wrapper.emitted()).toHaveProperty('click')
  })
})
```

### 10.3 Store 테스트

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

## 참고 문서

- **[Frontend README.md](README.md)** - 프로젝트 구조 및 환경
- **[docs/API.md](../../docs/API.md)** - Backend API 명세
- **[docs/PATTERNS.md](../../docs/PATTERNS.md)** - 공통 패턴

---

## 체크리스트

**코드 작성 전:**
- [ ] Frontend README.md 읽기
- [ ] docs/API.md 확인
- [ ] 이 CODE_GUIDE.md 패턴 확인

**코드 작성 시:**
- [ ] `<script setup>` 사용
- [ ] Pinia Setup Store 패턴
- [ ] Feature-Sliced Design 구조
- [ ] Zod 폼 검증
- [ ] try-catch 에러 핸들링
- [ ] Tailwind CSS 사용

**코드 작성 후:**
- [ ] `npm run lint` 통과
- [ ] `npm run format` 실행
- [ ] `npm run test` 통과
- [ ] 브라우저 동작 확인
