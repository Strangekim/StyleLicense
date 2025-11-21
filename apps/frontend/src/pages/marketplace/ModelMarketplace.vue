/**
 * ModelMarketplace Page
 *
 * Search & Following Artist Page - Horizontal scroll sections
 * Top section: Recent/Popular styles
 * Bottom section: Following artists' styles
 */
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useModelsStore } from '@/stores/models'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/layout/AppLayout.vue'

const router = useRouter()
const { t } = useI18n()
const modelsStore = useModelsStore()
const authStore = useAuthStore()
const searchQuery = ref('')
const sortBy = ref('recent')
const followingArtists = ref(new Set()) // Track following status
const expandedDescriptions = ref(new Set()) // Track expanded descriptions

const toggleDescription = (modelId, event) => {
  event.stopPropagation()
  const newSet = new Set(expandedDescriptions.value)
  if (newSet.has(modelId)) {
    newSet.delete(modelId)
  } else {
    newSet.add(modelId)
  }
  expandedDescriptions.value = newSet
}

onMounted(async () => {
  // Load initial models (only completed styles)
  await modelsStore.fetchModels({ training_status: 'completed', sort: '-created_at' })
})

const handleCardClick = (modelId) => {
  router.push(`/models/${modelId}`)
}

const handleArtistClick = (artistId, event) => {
  event.stopPropagation()
  router.push(`/artist/${artistId}`)
}

const toggleFollow = async (artistId, event) => {
  event.stopPropagation()

  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }

  // Create a new Set to trigger reactivity
  const newSet = new Set(followingArtists.value)
  if (newSet.has(artistId)) {
    newSet.delete(artistId)
    // TODO: Call API to unfollow
  } else {
    newSet.add(artistId)
    // TODO: Call API to follow
  }
  followingArtists.value = newSet
}

const toggleBookmark = async (modelId, event) => {
  event.stopPropagation()

  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }

  // TODO: Call API to bookmark/unbookmark
  console.log('Toggle bookmark for model:', modelId)
}

// Filter and sort models for top section (recent/popular)
const recentOrPopularModels = computed(() => {
  let filtered = modelsStore.models

  // Filter by search query
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(model =>
      model.name?.toLowerCase().includes(query) ||
      model.description?.toLowerCase().includes(query) ||
      model.artist?.username?.toLowerCase().includes(query)
    )
  }

  // Sort
  if (sortBy.value === 'recent') {
    filtered = [...filtered].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
  } else if (sortBy.value === 'popular') {
    filtered = [...filtered].sort((a, b) => b.usage_count - a.usage_count)
  }

  return filtered
})

// Filter models from following artists only
const followingModels = computed(() => {
  if (!authStore.isAuthenticated) return []

  let filtered = modelsStore.models.filter(model =>
    followingArtists.value.has(model.artist?.id)
  )

  // Apply search filter
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(model =>
      model.name?.toLowerCase().includes(query) ||
      model.description?.toLowerCase().includes(query) ||
      model.artist?.username?.toLowerCase().includes(query)
    )
  }

  // Sort by recent
  return [...filtered].sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
})
</script>

<template>
  <div class="min-h-screen bg-white">
    <AppLayout>
      <div class="max-w-screen-lg mx-auto">
        <!-- Search Bar -->
        <div class="sticky top-0 z-30 bg-white border-b border-neutral-100 px-4 py-3">
          <div class="max-w-screen-sm mx-auto">
            <div class="relative">
              <svg class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-neutral-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z"></path>
              </svg>
              <input
                v-model="searchQuery"
                type="text"
                :placeholder="t('marketplace.search')"
                class="w-full pl-10 pr-4 py-2 bg-neutral-100 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500"
              />
            </div>
          </div>
        </div>

        <!-- Sort Dropdown -->
        <div class="px-4 py-2 flex justify-end">
          <div class="max-w-screen-sm mx-auto w-full flex justify-end">
            <select
              v-model="sortBy"
              class="text-sm font-medium text-neutral-900 bg-transparent border-none focus:outline-none cursor-pointer"
            >
              <option value="recent">{{ t('marketplace.recent') }}</option>
              <option value="popular">{{ t('marketplace.popular') }}</option>
            </select>
          </div>
        </div>

        <!-- Recent/Popular Section (Horizontal Scroll) -->
        <div class="mb-8">
          <div v-if="recentOrPopularModels.length > 0" class="overflow-x-auto px-4">
        <div class="flex gap-3 pb-4" style="width: max-content;">
          <div
            v-for="model in recentOrPopularModels"
            :key="model.id"
            class="bg-white rounded-lg overflow-hidden cursor-pointer"
            style="width: 45vw; max-width: 280px; min-width: 180px; flex-shrink: 0;"
            @click="handleCardClick(model.id)"
          >
            <!-- Style Image with Carousel Dots -->
            <div class="relative aspect-square bg-neutral-100">
              <img
                :src="model.thumbnail_url || model.sample_images?.[0]"
                :alt="model.name"
                class="w-full h-full object-cover"
              />
              <!-- Carousel Dots -->
              <div class="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                <div
                  v-for="i in (model.sample_images?.length || 1)"
                  :key="i"
                  class="w-1.5 h-1.5 rounded-full"
                  :class="i === 1 ? 'bg-white' : 'bg-white/50'"
                ></div>
              </div>
              <!-- Bookmark Icon -->
              <button
                class="absolute top-2 right-2 p-1.5 bg-white/90 rounded-full"
                @click="toggleBookmark(model.id, $event)"
              >
                <svg class="w-4 h-4 text-neutral-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
                </svg>
              </button>
            </div>

            <!-- Card Content -->
            <div class="p-3 flex flex-col" style="min-height: 180px;">
              <!-- Artist Name -->
              <h3
                class="font-semibold text-sm text-neutral-900 mb-1 cursor-pointer hover:underline truncate"
                @click="handleArtistClick(model.artist?.id, $event)"
              >
                {{ model.artist?.username || t('marketplace.unknownArtist') }}
              </h3>

              <!-- Description -->
              <div class="mb-0.5 flex-grow">
                <p
                  class="text-xs text-neutral-600"
                  :class="expandedDescriptions.has(model.id) ? '' : 'line-clamp-2'"
                >
                  {{ model.description || t('marketplace.noDescription') }}
                  <span v-if="model.artist?.username" class="text-primary-500">
                    @{{ model.artist.username }}
                  </span>
                </p>
                <button
                  v-if="(model.description?.length || 0) > 60"
                  @click="toggleDescription(model.id, $event)"
                  class="text-xs text-neutral-500 hover:text-neutral-700 mt-1"
                >
                  {{ expandedDescriptions.has(model.id) ? t('marketplace.less') : t('marketplace.more') }}
                </button>
              </div>

              <!-- Model Name -->
              <p class="text-xs text-neutral-500 mb-3 truncate">
                {{ model.name }}
              </p>

              <!-- Styled by Section -->
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 flex-1 min-w-0">
                  <span class="text-xs italic text-neutral-900 flex-shrink-0" style="font-family: 'Brush Script MT', cursive;">
                    {{ t('marketplace.styledBy') }}
                  </span>
                  <div class="flex items-center gap-1.5 min-w-0">
                    <!-- Artist Avatar -->
                    <div class="w-5 h-5 rounded-full bg-neutral-200 flex items-center justify-center overflow-hidden flex-shrink-0">
                      <span class="text-xs font-semibold text-neutral-700">
                        {{ model.artist?.username?.charAt(0).toUpperCase() || 'A' }}
                      </span>
                    </div>
                    <!-- Artist Name -->
                    <span class="text-xs font-semibold text-neutral-900 truncate">
                      {{ model.artist?.username || t('marketplace.artist') }}
                    </span>
                  </div>
                </div>

                <!-- Following Button -->
                <button
                  v-if="model.artist?.id !== authStore.user?.id"
                  class="px-3 py-1 rounded-md text-xs font-medium transition-colors flex-shrink-0"
                  :class="followingArtists.has(model.artist?.id)
                    ? 'bg-neutral-200 text-neutral-900'
                    : 'bg-primary-500 text-white'"
                  @click="toggleFollow(model.artist?.id, $event)"
                >
                  {{ followingArtists.has(model.artist?.id) ? t('marketplace.following') : t('marketplace.follow') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Empty State -->
      <div v-else-if="!modelsStore.loading" class="py-10 text-center px-4">
        <svg class="mx-auto h-12 w-12 text-neutral-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
        </svg>
        <p class="text-neutral-500 text-sm">{{ t('marketplace.noStylesFound') }}</p>
        <p class="text-neutral-400 text-xs mt-1">{{ t('marketplace.tryAdjusting') }}</p>
      </div>

      <!-- Loading spinner -->
      <div v-if="modelsStore.loading && recentOrPopularModels.length === 0" class="flex justify-center items-center py-10">
        <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent"></div>
      </div>
    </div>

        <!-- Following Artists Section (Horizontal Scroll) -->
        <div v-if="authStore.isAuthenticated && followingModels.length > 0" class="mb-8">
      <h2 class="text-sm font-semibold text-neutral-900 px-4 mb-3">{{ t('marketplace.followingArtists') }}</h2>
      <div class="overflow-x-auto -mx-4 px-4">
        <div class="flex gap-3 pb-4" style="width: max-content;">
          <div
            v-for="model in followingModels"
            :key="`following-${model.id}`"
            class="bg-white rounded-lg overflow-hidden cursor-pointer"
            style="width: 45vw; max-width: 280px; min-width: 180px; flex-shrink: 0;"
            @click="handleCardClick(model.id)"
          >
            <!-- Style Image with Carousel Dots -->
            <div class="relative aspect-square bg-neutral-100">
              <img
                :src="model.thumbnail_url || model.sample_images?.[0]"
                :alt="model.name"
                class="w-full h-full object-cover"
              />
              <!-- Carousel Dots -->
              <div class="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                <div
                  v-for="i in (model.sample_images?.length || 1)"
                  :key="i"
                  class="w-1.5 h-1.5 rounded-full"
                  :class="i === 1 ? 'bg-white' : 'bg-white/50'"
                ></div>
              </div>
              <!-- Bookmark Icon -->
              <button
                class="absolute top-2 right-2 p-1.5 bg-white/90 rounded-full"
                @click="toggleBookmark(model.id, $event)"
              >
                <svg class="w-4 h-4 text-neutral-900" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
                </svg>
              </button>
            </div>

            <!-- Card Content -->
            <div class="p-3 flex flex-col" style="min-height: 180px;">
              <!-- Artist Name -->
              <h3
                class="font-semibold text-sm text-neutral-900 mb-1 cursor-pointer hover:underline truncate"
                @click="handleArtistClick(model.artist?.id, $event)"
              >
                {{ model.artist?.username || t('marketplace.unknownArtist') }}
              </h3>

              <!-- Description -->
              <div class="mb-0.5 flex-grow">
                <p
                  class="text-xs text-neutral-600"
                  :class="expandedDescriptions.has(model.id) ? '' : 'line-clamp-2'"
                >
                  {{ model.description || t('marketplace.noDescription') }}
                  <span v-if="model.artist?.username" class="text-primary-500">
                    @{{ model.artist.username }}
                  </span>
                </p>
                <button
                  v-if="(model.description?.length || 0) > 60"
                  @click="toggleDescription(model.id, $event)"
                  class="text-xs text-neutral-500 hover:text-neutral-700 mt-1"
                >
                  {{ expandedDescriptions.has(model.id) ? t('marketplace.less') : t('marketplace.more') }}
                </button>
              </div>

              <!-- Model Name -->
              <p class="text-xs text-neutral-500 mb-3 truncate">
                {{ model.name }}
              </p>

              <!-- Styled by Section -->
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-2 flex-1 min-w-0">
                  <span class="text-xs italic text-neutral-900 flex-shrink-0" style="font-family: 'Brush Script MT', cursive;">
                    Styled by
                  </span>
                  <div class="flex items-center gap-1.5 min-w-0">
                    <!-- Artist Avatar -->
                    <div class="w-5 h-5 rounded-full bg-neutral-200 flex items-center justify-center overflow-hidden flex-shrink-0">
                      <span class="text-xs font-semibold text-neutral-700">
                        {{ model.artist?.username?.charAt(0).toUpperCase() || 'A' }}
                      </span>
                    </div>
                    <!-- Artist Name -->
                    <span class="text-xs font-semibold text-neutral-900 truncate">
                      {{ model.artist?.username || 'Artist' }}
                    </span>
                  </div>
                </div>

                <!-- Following Button -->
                <button
                  class="px-3 py-1 rounded-md text-xs font-medium transition-colors flex-shrink-0 bg-neutral-200 text-neutral-900"
                  @click="toggleFollow(model.artist?.id, $event)"
                >
                  {{ t('marketplace.following') }}
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
      </div>
    </AppLayout>
  </div>
</template>
