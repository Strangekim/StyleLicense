/**
 * GenerationHistory Page
 *
 * Displays user's generation history with filtering and infinite scroll.
 */
<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useGenerationStore } from '@/stores/generations'
import AppLayout from '@/components/layout/AppLayout.vue'
import Button from '@/components/shared/Button.vue'
import ImagePreview from '@/components/features/generation/ImagePreview.vue'

const router = useRouter()
const generationStore = useGenerationStore()

// Filter state
const selectedStatus = ref('all') // 'all', 'completed', 'failed', 'processing'

// UI state
const loadMoreTrigger = ref(null)
let observer = null

// Computed
const generations = computed(() => generationStore.generations)
const isLoading = computed(() => generationStore.loading)
const hasMore = computed(() => generationStore.hasMore)
const error = computed(() => generationStore.error)

// Filter generations by status
const filteredGenerations = computed(() => {
  if (selectedStatus.value === 'all') {
    return generations.value
  }
  return generations.value.filter((g) => g.status === selectedStatus.value)
})

// Status options
const statusOptions = [
  { value: 'all', label: 'All' },
  { value: 'completed', label: 'Completed' },
  { value: 'processing', label: 'Processing' },
  { value: 'failed', label: 'Failed' },
]

// Fetch generations
const fetchGenerations = async (append = false) => {
  const params = {}

  if (selectedStatus.value !== 'all') {
    params.status = selectedStatus.value
  }

  await generationStore.fetchGenerations(params, append)
}

// Load more for infinite scroll
const handleLoadMore = () => {
  if (!isLoading.value && hasMore.value) {
    generationStore.loadMore()
  }
}

// Setup intersection observer for infinite scroll
const setupInfiniteScroll = () => {
  if (observer) {
    observer.disconnect()
  }

  observer = new IntersectionObserver(
    (entries) => {
      const [entry] = entries
      if (entry.isIntersecting) {
        handleLoadMore()
      }
    },
    { threshold: 0.1 }
  )

  if (loadMoreTrigger.value) {
    observer.observe(loadMoreTrigger.value)
  }
}

// Cleanup observer
const cleanupInfiniteScroll = () => {
  if (observer) {
    observer.disconnect()
  }
}

// Handle regenerate
const handleRegenerate = (params) => {
  router.push({
    path: '/generate',
    query: {
      styleId: params.style_id,
    },
  })
}

// Handle delete
const handleDelete = async (id) => {
  // TODO: Implement delete generation API
  console.log('Delete generation:', id)
}

// Lifecycle
onMounted(async () => {
  await fetchGenerations(false)

  setTimeout(() => {
    setupInfiniteScroll()
  }, 100)
})

onUnmounted(() => {
  cleanupInfiniteScroll()
})

// Watch filter changes
const handleFilterChange = async () => {
  await fetchGenerations(false)
}
</script>

<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Page Header -->
      <div class="mb-8 flex items-center justify-between">
        <div>
          <h1 class="text-3xl font-bold text-neutral-900 mb-2">
            Generation History
          </h1>
          <p class="text-neutral-600">
            View and manage your past generations
          </p>
        </div>
        <Button variant="primary" @click="router.push('/generate')">
          New Generation
        </Button>
      </div>

      <!-- Filters -->
      <div class="mb-6 flex gap-2">
        <button
          v-for="option in statusOptions"
          :key="option.value"
          class="px-4 py-2 rounded-lg text-sm font-medium transition-colors"
          :class="{
            'bg-primary-600 text-white': selectedStatus === option.value,
            'bg-neutral-100 text-neutral-700 hover:bg-neutral-200': selectedStatus !== option.value,
          }"
          @click="selectedStatus = option.value; handleFilterChange()"
        >
          {{ option.label }}
        </button>
      </div>

      <!-- Error State -->
      <div v-if="error" class="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-red-800">{{ error }}</p>
        <Button variant="outline" size="sm" class="mt-2" @click="fetchGenerations(false)">
          Retry
        </Button>
      </div>

      <!-- Loading State (Initial) -->
      <div v-if="isLoading && filteredGenerations.length === 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6">
        <div
          v-for="n in 6"
          :key="n"
          class="animate-pulse"
        >
          <div class="aspect-square bg-neutral-200 rounded-lg mb-3"></div>
          <div class="h-4 bg-neutral-200 rounded mb-2"></div>
          <div class="h-3 bg-neutral-200 rounded w-2/3"></div>
        </div>
      </div>

      <!-- Generations Grid -->
      <div
        v-else-if="filteredGenerations.length > 0"
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-6"
      >
        <ImagePreview
          v-for="generation in filteredGenerations"
          :key="generation.id"
          :generation="generation"
          @regenerate="handleRegenerate"
          @delete="handleDelete"
        />
      </div>

      <!-- Empty State -->
      <div v-else class="text-center py-16">
        <svg
          class="w-16 h-16 text-neutral-400 mx-auto mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"
          />
        </svg>
        <h3 class="text-lg font-semibold text-neutral-900 mb-2">
          No generations found
        </h3>
        <p class="text-neutral-600 mb-4">
          {{ selectedStatus === 'all' ? 'You haven\'t generated any images yet' : `No ${selectedStatus} generations` }}
        </p>
        <Button variant="primary" @click="router.push('/generate')">
          Generate Your First Image
        </Button>
      </div>

      <!-- Infinite Scroll Trigger -->
      <div
        v-if="hasMore"
        ref="loadMoreTrigger"
        class="flex justify-center py-8"
      >
        <div class="flex items-center gap-2 text-neutral-600">
          <svg
            class="animate-spin h-5 w-5"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            ></circle>
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            ></path>
          </svg>
          <span>Loading more...</span>
        </div>
      </div>

      <!-- End of List Message -->
      <div
        v-else-if="filteredGenerations.length > 0"
        class="text-center py-8 text-neutral-500"
      >
        You've reached the end of the list
      </div>
    </div>
  </AppLayout>
</template>
