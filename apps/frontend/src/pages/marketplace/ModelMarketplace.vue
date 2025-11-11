/**
 * ModelMarketplace Page
 *
 * Displays a grid of available style models with search, filter, and infinite scroll.
 * Public access - no authentication required.
 */
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useModelsStore } from '@/stores/models'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'
import ModelCard from '@/components/features/model/ModelCard.vue'
import Input from '@/components/shared/Input.vue'
import Button from '@/components/shared/Button.vue'

const router = useRouter()
const modelsStore = useModelsStore()

// Search and filter state
const searchQuery = ref('')
const selectedSort = ref('popular') // 'popular' or 'recent'
const selectedTags = ref([])
const isFilterOpen = ref(false)

// Debounce timer
let searchDebounceTimer = null

// Computed
const isLoading = computed(() => modelsStore.loading)
const models = computed(() => modelsStore.models)
const hasMore = computed(() => modelsStore.hasMore)
const error = computed(() => modelsStore.error)

// Infinite scroll observer
let observer = null
const loadMoreTrigger = ref(null)

// Fetch models with current filters
const fetchModels = async (append = false) => {
  const params = {}

  // Add search query
  if (searchQuery.value.trim()) {
    params.search = searchQuery.value.trim()
  }

  // Add tags filter
  if (selectedTags.value.length > 0) {
    params.tags = selectedTags.value.join(',')
  }

  // Add sort
  params.sort = selectedSort.value === 'popular' ? '-usage_count' : '-created_at'

  // Only show completed models
  params.training_status = 'completed'

  await modelsStore.fetchModels(params, append)
}

// Search with debounce
const handleSearch = () => {
  clearTimeout(searchDebounceTimer)
  searchDebounceTimer = setTimeout(() => {
    fetchModels(false)
  }, 500)
}

// Watch for search query changes
watch(searchQuery, handleSearch)

// Watch for sort changes
watch(selectedSort, () => {
  fetchModels(false)
})

// Watch for tag changes
watch(selectedTags, () => {
  fetchModels(false)
}, { deep: true })

// Load more for infinite scroll
const handleLoadMore = () => {
  if (!isLoading.value && hasMore.value) {
    modelsStore.loadMore()
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

// Lifecycle
onMounted(async () => {
  // Fetch initial models
  await fetchModels(false)

  // Setup infinite scroll after initial load
  setTimeout(() => {
    setupInfiniteScroll()
  }, 100)
})

// Cleanup on unmount
import { onUnmounted } from 'vue'
onUnmounted(() => {
  cleanupInfiniteScroll()
})

// Clear filters
const clearFilters = () => {
  searchQuery.value = ''
  selectedTags.value = []
  selectedSort.value = 'popular'
}
</script>

<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Page Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-neutral-900 mb-2">
          Style Marketplace
        </h1>
        <p class="text-neutral-600">
          Discover unique AI art styles from talented artists
        </p>
      </div>

      <!-- Search and Filters -->
      <div class="mb-8 space-y-4">
        <!-- Search Bar -->
        <div class="flex gap-4">
          <div class="flex-1">
            <Input
              v-model="searchQuery"
              type="text"
              placeholder="Search styles..."
            >
              <template #prefix>
                <svg
                  class="w-5 h-5 text-neutral-400"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"
                  />
                </svg>
              </template>
            </Input>
          </div>

          <!-- Sort Dropdown -->
          <select
            v-model="selectedSort"
            class="px-4 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent bg-white"
          >
            <option value="popular">Most Popular</option>
            <option value="recent">Most Recent</option>
          </select>

          <!-- Clear Filters Button -->
          <Button
            v-if="searchQuery || selectedTags.length > 0"
            variant="outline"
            @click="clearFilters"
          >
            Clear Filters
          </Button>
        </div>

        <!-- Active Filters Display -->
        <div v-if="selectedTags.length > 0" class="flex flex-wrap gap-2">
          <span class="text-sm text-neutral-600">Active filters:</span>
          <button
            v-for="tag in selectedTags"
            :key="tag"
            class="px-3 py-1 bg-primary-100 text-primary-700 rounded-full text-sm flex items-center gap-1 hover:bg-primary-200 transition-colors"
            @click="selectedTags = selectedTags.filter(t => t !== tag)"
          >
            {{ tag }}
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Error State -->
      <div v-if="error" class="mb-8 p-4 bg-red-50 border border-red-200 rounded-lg">
        <p class="text-red-800">{{ error }}</p>
        <Button variant="outline" size="sm" class="mt-2" @click="fetchModels(false)">
          Retry
        </Button>
      </div>

      <!-- Loading State (Initial) -->
      <div v-if="isLoading && models.length === 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <div
          v-for="n in 8"
          :key="n"
          class="animate-pulse"
        >
          <div class="aspect-square bg-neutral-200 rounded-lg mb-3"></div>
          <div class="h-4 bg-neutral-200 rounded mb-2"></div>
          <div class="h-3 bg-neutral-200 rounded w-2/3"></div>
        </div>
      </div>

      <!-- Models Grid -->
      <div
        v-else-if="models.length > 0"
        class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6"
      >
        <ModelCard
          v-for="model in models"
          :key="model.id"
          :model="model"
        />
      </div>

      <!-- Empty State -->
      <div
        v-else
        class="text-center py-16"
      >
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
            d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h3 class="text-lg font-semibold text-neutral-900 mb-2">
          No styles found
        </h3>
        <p class="text-neutral-600 mb-4">
          Try adjusting your search or filters
        </p>
        <Button variant="outline" @click="clearFilters">
          Clear Filters
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
          <span>Loading more styles...</span>
        </div>
      </div>

      <!-- End of List Message -->
      <div
        v-else-if="models.length > 0"
        class="text-center py-8 text-neutral-500"
      >
        You've reached the end of the list
      </div>
    </div>
  </AppLayout>
</template>
