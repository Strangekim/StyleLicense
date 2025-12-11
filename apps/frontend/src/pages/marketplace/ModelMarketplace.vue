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
import { useModelsStore } from '@/stores/models'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/layout/AppLayout.vue'
import { toggleFollow, getFollowingList } from '@/services/user.service'

const router = useRouter()
const modelsStore = useModelsStore()
const authStore = useAuthStore()
const searchQuery = ref('')
const sortBy = ref('recent')
const followingArtists = ref(new Set()) // Track following status
const expandedDescriptions = ref(new Set()) // Track expanded descriptions
const currentImageIndexMap = ref(new Map()) // Track current image index for each model

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

const getCurrentImageIndex = (section, modelId) => {
  const key = `${section}-${modelId}`
  return currentImageIndexMap.value.get(key) || 0
}

const setImageIndex = (section, modelId, index, event) => {
  event.stopPropagation()
  const key = `${section}-${modelId}`
  const newMap = new Map(currentImageIndexMap.value)
  newMap.set(key, index)
  currentImageIndexMap.value = newMap
}

const nextImage = (section, modelId, totalImages, event) => {
  event.stopPropagation()
  const currentIndex = getCurrentImageIndex(section, modelId)
  const newIndex = (currentIndex + 1) % totalImages
  setImageIndex(section, modelId, newIndex, event)
}

const prevImage = (section, modelId, totalImages, event) => {
  event.stopPropagation()
  const currentIndex = getCurrentImageIndex(section, modelId)
  const newIndex = (currentIndex - 1 + totalImages) % totalImages
  setImageIndex(section, modelId, newIndex, event)
}

onMounted(async () => {
  // Load initial models (only completed styles)
  await modelsStore.fetchModels({ training_status: 'completed', sort: '-created_at' })

  // Load following artists list if authenticated
  if (authStore.isAuthenticated) {
    try {
      const followingData = await getFollowingList()
      const followingIds = followingData.results?.map(user => user.id) || []
      followingArtists.value = new Set(followingIds)
    } catch (error) {
      console.error('Failed to fetch following list:', error)
    }
  }
})

const handleCardClick = (modelId) => {
  router.push(`/models/${modelId}`)
}

const handleArtistClick = (artistId, event) => {
  event.stopPropagation()
  router.push(`/artist/${artistId}`)
}

const handleToggleFollow = async (artistId, event) => {
  event.stopPropagation()

  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }

  try {
    // Call follow API
    const response = await toggleFollow(artistId)

    // Update local state
    const newSet = new Set(followingArtists.value)
    if (response.is_following) {
      newSet.add(artistId)
    } else {
      newSet.delete(artistId)
    }
    followingArtists.value = newSet
  } catch (error) {
    console.error('Failed to toggle follow:', error)
  }
}

const toggleBookmark = async (model, event) => {
  event.stopPropagation()

  if (!authStore.isAuthenticated) {
    router.push('/login')
    return
  }

  // Get artist ID from the model
  const artistId = model.artist_id
  if (!artistId) {
    console.error('Artist ID not found')
    return
  }

  // Don't allow following yourself
  if (artistId === authStore.user?.id) {
    console.log('Cannot follow yourself')
    return
  }

  try {
    // Call follow API
    const response = await toggleFollow(artistId)

    // Update local state
    const newSet = new Set(followingArtists.value)
    if (response.is_following) {
      newSet.add(artistId)
    } else {
      newSet.delete(artistId)
    }
    followingArtists.value = newSet
  } catch (error) {
    console.error('Failed to toggle follow:', error)
  }
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
      model.artist_username?.toLowerCase().includes(query)
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
    followingArtists.value.has(model.artist_id)
  )

  // Apply search filter
  if (searchQuery.value.trim()) {
    const query = searchQuery.value.toLowerCase()
    filtered = filtered.filter(model =>
      model.name?.toLowerCase().includes(query) ||
      model.description?.toLowerCase().includes(query) ||
      model.artist_username?.toLowerCase().includes(query)
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
                :placeholder="$t('marketplace.search')"
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
              <option value="recent">{{ $t('marketplace.recent') }}</option>
              <option value="popular">{{ $t('marketplace.popular') }}</option>
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
            <!-- Style Image with Carousel -->
            <div class="relative aspect-square bg-neutral-100">
              <img
                :src="model.sample_images?.[getCurrentImageIndex('recent', model.id)] || model.thumbnail_url"
                :alt="model.name"
                class="w-full h-full object-cover"
              />

              <!-- Previous Button -->
              <button
                v-if="model.sample_images && model.sample_images.length > 1"
                @click="prevImage('recent', model.id, model.sample_images.length, $event)"
                class="absolute left-1 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-black/50 hover:bg-black/70 flex items-center justify-center text-white transition-colors"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
                </svg>
              </button>

              <!-- Next Button -->
              <button
                v-if="model.sample_images && model.sample_images.length > 1"
                @click="nextImage('recent', model.id, model.sample_images.length, $event)"
                class="absolute right-1 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-black/50 hover:bg-black/70 flex items-center justify-center text-white transition-colors"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </button>

              <!-- Carousel Dots -->
              <div v-if="model.sample_images && model.sample_images.length > 1" class="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                <button
                  v-for="(img, index) in model.sample_images"
                  :key="index"
                  @click="setImageIndex('recent', model.id, index, $event)"
                  class="w-1.5 h-1.5 rounded-full transition-all"
                  :class="getCurrentImageIndex('recent', model.id) === index ? 'bg-white w-4' : 'bg-white/50'"
                ></button>
              </div>

              <!-- Bookmark Icon (Follow Artist) -->
              <button
                v-if="authStore.user?.id !== model.artist_id"
                class="absolute top-2 right-2 p-1.5 bg-white/90 rounded-full hover:bg-white transition-colors"
                @click="toggleBookmark(model, $event)"
              >
                <svg
                  class="w-4 h-4 text-neutral-900"
                  :fill="followingArtists.has(model.artist_id) ? 'currentColor' : 'none'"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
                </svg>
              </button>
            </div>

            <!-- Card Content -->
            <div class="p-3 flex flex-col" style="min-height: 180px;">
              <!-- Artist Name -->
              <h3
                class="font-semibold text-sm text-neutral-900 mb-1 cursor-pointer hover:underline truncate"
                @click="handleArtistClick(model.artist_id, $event)"
              >
                {{ model.artist_username || $t('marketplace.unknownArtist') }}
              </h3>

              <!-- Description -->
              <div class="mb-0.5 flex-grow">
                <p
                  class="text-xs text-neutral-600"
                  :class="expandedDescriptions.has(model.id) ? '' : 'line-clamp-2'"
                >
                  {{ model.description || $t('marketplace.noDescription') }}
                  <span v-if="model.artist_username" class="text-primary-500">
                    @{{ model.artist_username }}
                  </span>
                </p>
                <button
                  v-if="(model.description?.length || 0) > 60"
                  @click="toggleDescription(model.id, $event)"
                  class="text-xs text-neutral-500 hover:text-neutral-700 mt-1"
                >
                  {{ expandedDescriptions.has(model.id) ? $t('marketplace.less') : $t('marketplace.more') }}
                </button>
              </div>

              <!-- Model Name -->
              <p class="text-xs text-neutral-500 mb-3 truncate">
                {{ model.name }}
              </p>

              <!-- Styled by Section -->
              <div class="flex items-center justify-end gap-2">
                <span class="text-xs italic text-neutral-900 flex-shrink-0" style="font-family: 'Brush Script MT', cursive;">
                  Styled by
                </span>
                <!-- Artist Avatar -->
                <div class="w-5 h-5 rounded-full bg-neutral-200 flex items-center justify-center overflow-hidden flex-shrink-0">
                  <img
                    v-if="model.artist_profile_image"
                    :src="model.artist_profile_image"
                    alt="Artist profile"
                    class="w-full h-full object-cover"
                  />
                  <span v-else class="text-xs font-semibold text-neutral-700">
                    {{ model.artist_username?.charAt(0).toUpperCase() || 'A' }}
                  </span>
                </div>
                <!-- Artist Name -->
                <span class="text-xs font-semibold text-neutral-900 truncate">
                  {{ model.artist_username || $t('marketplace.artist') }}
                </span>
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
        <p class="text-neutral-500 text-sm">{{ $t('marketplace.noStylesFound') }}</p>
        <p class="text-neutral-400 text-xs mt-1">{{ $t('marketplace.tryAdjusting') }}</p>
      </div>

      <!-- Loading spinner -->
      <div v-if="modelsStore.loading && recentOrPopularModels.length === 0" class="flex justify-center items-center py-10">
        <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent"></div>
      </div>
    </div>

        <!-- Following Artists Section (Horizontal Scroll) -->
        <div v-if="authStore.isAuthenticated && followingModels.length > 0" class="mb-8">
      <h2 class="text-sm font-semibold text-neutral-900 px-4 mb-3">{{ $t('marketplace.followingArtists') }}</h2>
      <div class="overflow-x-auto -mx-4 px-4">
        <div class="flex gap-3 pb-4" style="width: max-content;">
          <div
            v-for="model in followingModels"
            :key="`following-${model.id}`"
            class="bg-white rounded-lg overflow-hidden cursor-pointer"
            style="width: 45vw; max-width: 280px; min-width: 180px; flex-shrink: 0;"
            @click="handleCardClick(model.id)"
          >
            <!-- Style Image with Carousel -->
            <div class="relative aspect-square bg-neutral-100">
              <img
                :src="model.sample_images?.[getCurrentImageIndex('following', model.id)] || model.thumbnail_url"
                :alt="model.name"
                class="w-full h-full object-cover"
              />

              <!-- Previous Button -->
              <button
                v-if="model.sample_images && model.sample_images.length > 1"
                @click="prevImage('following', model.id, model.sample_images.length, $event)"
                class="absolute left-1 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-black/50 hover:bg-black/70 flex items-center justify-center text-white transition-colors"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
                </svg>
              </button>

              <!-- Next Button -->
              <button
                v-if="model.sample_images && model.sample_images.length > 1"
                @click="nextImage('following', model.id, model.sample_images.length, $event)"
                class="absolute right-1 top-1/2 -translate-y-1/2 w-6 h-6 rounded-full bg-black/50 hover:bg-black/70 flex items-center justify-center text-white transition-colors"
              >
                <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
                </svg>
              </button>

              <!-- Carousel Dots -->
              <div v-if="model.sample_images && model.sample_images.length > 1" class="absolute bottom-2 left-1/2 -translate-x-1/2 flex gap-1">
                <button
                  v-for="(img, index) in model.sample_images"
                  :key="index"
                  @click="setImageIndex('following', model.id, index, $event)"
                  class="w-1.5 h-1.5 rounded-full transition-all"
                  :class="getCurrentImageIndex('following', model.id) === index ? 'bg-white w-4' : 'bg-white/50'"
                ></button>
              </div>

              <!-- Bookmark Icon (Follow Artist) -->
              <button
                v-if="authStore.user?.id !== model.artist_id"
                class="absolute top-2 right-2 p-1.5 bg-white/90 rounded-full hover:bg-white transition-colors"
                @click="toggleBookmark(model, $event)"
              >
                <svg
                  class="w-4 h-4 text-neutral-900"
                  :fill="followingArtists.has(model.artist_id) ? 'currentColor' : 'none'"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
                </svg>
              </button>
            </div>

            <!-- Card Content -->
            <div class="p-3 flex flex-col" style="min-height: 180px;">
              <!-- Artist Name -->
              <h3
                class="font-semibold text-sm text-neutral-900 mb-1 cursor-pointer hover:underline truncate"
                @click="handleArtistClick(model.artist_id, $event)"
              >
                {{ model.artist_username || $t('marketplace.unknownArtist') }}
              </h3>

              <!-- Description -->
              <div class="mb-0.5 flex-grow">
                <p
                  class="text-xs text-neutral-600"
                  :class="expandedDescriptions.has(model.id) ? '' : 'line-clamp-2'"
                >
                  {{ model.description || $t('marketplace.noDescription') }}
                  <span v-if="model.artist_username" class="text-primary-500">
                    @{{ model.artist_username }}
                  </span>
                </p>
                <button
                  v-if="(model.description?.length || 0) > 60"
                  @click="toggleDescription(model.id, $event)"
                  class="text-xs text-neutral-500 hover:text-neutral-700 mt-1"
                >
                  {{ expandedDescriptions.has(model.id) ? $t('marketplace.less') : $t('marketplace.more') }}
                </button>
              </div>

              <!-- Model Name -->
              <p class="text-xs text-neutral-500 mb-3 truncate">
                {{ model.name }}
              </p>

              <!-- Styled by Section -->
              <div class="flex items-center justify-end gap-2">
                <span class="text-xs italic text-neutral-900 flex-shrink-0" style="font-family: 'Brush Script MT', cursive;">
                  Styled by
                </span>
                <!-- Artist Avatar -->
                <div class="w-5 h-5 rounded-full bg-neutral-200 flex items-center justify-center overflow-hidden flex-shrink-0">
                  <img
                    v-if="model.artist_profile_image"
                    :src="model.artist_profile_image"
                    alt="Artist profile"
                    class="w-full h-full object-cover"
                  />
                  <span v-else class="text-xs font-semibold text-neutral-700">
                    {{ model.artist_username?.charAt(0).toUpperCase() || 'A' }}
                  </span>
                </div>
                <!-- Artist Name -->
                <span class="text-xs font-semibold text-neutral-900 truncate">
                  {{ model.artist_username || $t('marketplace.artist') }}
                </span>
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
