/**
 * StyleDetail Page (Unified Model Detail + Generation)
 *
 * Based on StyleDetailPage1-4 mockups
 * Combines style information viewing and image generation in a single scrollable page
 */
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useModelsStore } from '@/stores/models'
import { useGenerationStore } from '@/stores/generations'
import { useTokenStore } from '@/stores/tokens'
import { useAuthStore } from '@/stores/auth'
import { useAlertStore } from '@/stores/alert'
import AppLayout from '@/components/layout/AppLayout.vue'
import TagButton from '@/components/shared/TagButton.vue'
import { toggleFollow, getFollowingList } from '@/services/user.service'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const modelsStore = useModelsStore()
const generationStore = useGenerationStore()
const tokenStore = useTokenStore()
const authStore = useAuthStore()
const alertStore = useAlertStore()

// State
const modelId = computed(() => parseInt(route.params.id))
const model = computed(() => modelsStore.currentModel)
const isLoading = computed(() => modelsStore.loading)
const currentImageIndex = ref(0)
const isBookmarked = ref(false)

// Generation form state
const prompt = ref('')
const newTagInput = ref('')
const userTags = ref([]) // User-created tags
const isGenerating = ref(false)
const showWarning = ref(false)
const selectedAspectRatio = ref('1:1') // Default aspect ratio
const tagError = ref(false) // Track non-English input attempt

// Aspect ratio options
const aspectRatioOptions = [
  { value: '1:1', icon: 'square' },
  { value: '2:2', icon: 'square-large' },
  { value: '1:2', icon: 'portrait' },
]

// Computed
const sampleImages = computed(() => {
  // Backend returns artworks array with image_url field
  const artworks = model.value?.artworks || []
  return artworks.map(artwork => artwork.image_url).filter(url => url)
})

const currentImage = computed(() => {
  return sampleImages.value[currentImageIndex.value] || null
})

// Training image tags: all backend caption tags (read-only)
const trainingTags = computed(() => {
  const backendTags = model.value?.tags || []

  // Extract tag names (tags can be objects with {id, name, sequence} or just strings)
  return backendTags.map(tag =>
    typeof tag === 'string' ? tag : tag.name
  )
})

// Generation tags: style name (default) + user-added tags (for generation prompt)
const generationTags = computed(() => {
  // Only use style name as the default tag (not other backend tags)
  const defaultTag = model.value?.name?.toLowerCase() || 'style'

  // Combine default tag with user-added tags (avoid duplicates)
  const allTagNames = [defaultTag]
  userTags.value.forEach(userTag => {
    if (userTag.toLowerCase() !== defaultTag) {
      allTagNames.push(userTag)
    }
  })

  return allTagNames
})

const canGenerate = computed(() => {
  return (
    model.value?.training_status === 'completed' &&
    generationTags.value.length > 0 &&
    !isGenerating.value &&
    authStore.isAuthenticated
  )
})

// Check if current user is the owner of this style
const isOwnStyle = computed(() => {
  return authStore.isAuthenticated && model.value?.artist_id === authStore.user?.id
})

// Format time ago
const formatTimeAgo = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const seconds = Math.floor((now - date) / 1000)

  if (seconds < 60) return t('styleDetail.justNow')
  if (seconds < 3600) return t('styleDetail.minutesAgo', { count: Math.floor(seconds / 60) })
  if (seconds < 86400) return t('styleDetail.hoursAgo', { count: Math.floor(seconds / 3600) })
  if (seconds < 604800) return t('styleDetail.daysAgo', { count: Math.floor(seconds / 86400) })
  return t('styleDetail.weeksAgo', { count: Math.floor(seconds / 604800) })
}

// Actions
const toggleBookmark = async () => {
  if (!authStore.isAuthenticated) {
    router.push(`/login?returnUrl=/models/${modelId.value}`)
    return
  }

  // Prevent following yourself
  if (isOwnStyle.value) {
    console.log('Cannot follow yourself')
    return
  }

  // Get artist ID from the model
  const artistId = model.value?.artist_id
  if (!artistId) {
    console.error('Artist ID not found')
    return
  }

  try {
    // Call follow API
    const response = await toggleFollow(artistId)
    isBookmarked.value = response.is_following
  } catch (error) {
    console.error('Failed to toggle follow:', error)
    if (error.response?.status === 400) {
      console.log('Cannot follow yourself or invalid request')
    }
  }
}

// Filter to allow only English letters and spaces
const filterTagEnglishOnly = (event) => {
  const input = event.target.value
  const filtered = input.replace(/[^a-zA-Z\s]/g, '')

  // Check if non-English characters were attempted
  if (input !== filtered) {
    tagError.value = true
    newTagInput.value = filtered
    // Trigger input event to update cursor position
    event.target.value = filtered
  } else {
    tagError.value = false
  }
}

const addNewTag = () => {
  const tagText = newTagInput.value.trim()
  if (!tagText) return

  // Validate English only
  const englishOnlyRegex = /^[a-zA-Z\s]*$/
  if (!englishOnlyRegex.test(tagText)) {
    alert(t('generation.errors.englishOnly'))
    return
  }

  // Check for inappropriate words
  const inappropriateWords = ['irrelevant', 'inappropriate', 'misleading']
  const hasInappropriate = inappropriateWords.some(word =>
    tagText.toLowerCase().includes(word)
  )

  if (hasInappropriate) {
    showWarning.value = true
    setTimeout(() => {
      showWarning.value = false
    }, 5000)
    return
  }

  // Add tag if not already exists
  if (!userTags.value.includes(tagText)) {
    userTags.value.push(tagText)
  }

  // Clear input and error state
  newTagInput.value = ''
  tagError.value = false
}

const removeTag = (index) => {
  // Can't remove the first tag (style name)
  if (index === 0) return

  // Remove from userTags (index - 1 because first tag is style name)
  const userTagIndex = index - 1
  if (userTagIndex >= 0 && userTagIndex < userTags.value.length) {
    userTags.value.splice(userTagIndex, 1)
  }
}

const handleGenerate = async () => {
  if (!canGenerate.value) {
    if (!authStore.isAuthenticated) {
      router.push(`/login?returnUrl=/models/${modelId.value}`)
    }
    return
  }

  // Check for inappropriate tags (simple validation)
  const inappropriateWords = ['irrelevant', 'inappropriate', 'misleading']
  const hasInappropriate = inappropriateWords.some(word =>
    prompt.value.toLowerCase().includes(word)
  )

  if (hasInappropriate) {
    showWarning.value = true
    setTimeout(() => {
      showWarning.value = false
    }, 5000)
    return
  }

  isGenerating.value = true

  try {
    // Generate random seed
    const randomSeed = Math.floor(Math.random() * 2147483647)

    const data = {
      style_id: modelId.value,
      prompt_tags: generationTags.value,
      description: '',
      aspect_ratio: selectedAspectRatio.value,
      seed: randomSeed,
    }

    await generationStore.generateImage(data)

    // Deduct tokens
    await tokenStore.fetchBalance()

    // Show success
    alertStore.show({
      type: 'success',
      title: t('alerts.generationSuccess.title'),
      message: t('alerts.generationSuccess.message'),
      confirmText: t('alerts.generationSuccess.confirmButton'),
      showCancel: false,
      onConfirm: () => {
        router.push('/profile')
      }
    })

    // Clear user tags (keep default tag)
    userTags.value = []
  } catch (error) {
    console.error('Generation failed:', error)

    // Don't show alert for 402 errors - API interceptor will handle it
    if (error.response?.status === 402) {
      // API interceptor already showed the insufficient tokens alert
      return
    }

    alertStore.show({
      type: 'error',
      title: t('alerts.error.title'),
      message: error.response?.data?.error?.message || t('alerts.generationFailed.message'),
      confirmText: t('alerts.error.confirmButton'),
      showCancel: false
    })
  } finally {
    isGenerating.value = false
  }
}

const navigateToArtist = () => {
  // Since each artist currently has only one style,
  // clicking artist name stays on the same style detail page
  if (model.value?.id) {
    router.push(`/marketplace/styles/${model.value.id}`)
  }
}

// Fetch model on mount
onMounted(async () => {
  try {
    await modelsStore.fetchModelDetail(modelId.value)

    // Fetch user balance if authenticated
    if (authStore.isAuthenticated) {
      await tokenStore.fetchBalance()

      // Check if current user is following the artist
      try {
        const followingData = await getFollowingList()
        const followingIds = followingData.results?.map(user => user.id) || []
        const artistId = modelsStore.currentModel?.artist_id
        if (artistId) {
          isBookmarked.value = followingIds.includes(artistId)
        }
      } catch (error) {
        console.error('Failed to fetch following list:', error)
      }
    }
  } catch (err) {
    console.error('Failed to fetch model detail:', err)
  }
})
</script>

<template>
  <div v-if="isLoading" class="flex justify-center items-center min-h-screen">
    <div class="animate-spin rounded-full h-8 w-8 border-2 border-primary-500 border-t-transparent"></div>
  </div>

  <div v-else-if="model" class="min-h-screen bg-white">
    <AppLayout>
    <!-- Training Image Section -->
    <div class="px-4 pt-3 pb-2">
      <h2 class="text-base font-semibold text-neutral-900">{{ $t('styleDetail.trainingImage') }}</h2>
    </div>

    <!-- Main Image with Carousel -->
    <div class="relative w-full aspect-square bg-neutral-100">
      <img
        v-if="currentImage"
        :src="currentImage"
        :alt="model.name"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center">
        <svg class="w-16 h-16 text-neutral-300" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z"></path>
        </svg>
      </div>

      <!-- Previous Button -->
      <button
        v-if="sampleImages.length > 1"
        @click="currentImageIndex = (currentImageIndex - 1 + sampleImages.length) % sampleImages.length"
        class="absolute left-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 hover:bg-black/70 flex items-center justify-center text-white transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7"></path>
        </svg>
      </button>

      <!-- Next Button -->
      <button
        v-if="sampleImages.length > 1"
        @click="currentImageIndex = (currentImageIndex + 1) % sampleImages.length"
        class="absolute right-2 top-1/2 -translate-y-1/2 w-8 h-8 rounded-full bg-black/50 hover:bg-black/70 flex items-center justify-center text-white transition-colors"
      >
        <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9 5l7 7-7 7"></path>
        </svg>
      </button>

      <!-- Carousel Dots -->
      <div v-if="sampleImages.length > 1" class="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-2">
        <button
          v-for="(image, index) in sampleImages"
          :key="index"
          @click="currentImageIndex = index"
          class="w-2 h-2 rounded-full transition-all"
          :class="currentImageIndex === index ? 'bg-white w-6' : 'bg-white/50'"
        ></button>
      </div>

      <!-- Image Counter -->
      <div v-if="sampleImages.length > 1" class="absolute top-3 right-3 px-2 py-1 rounded-full bg-black/50 text-white text-xs">
        {{ currentImageIndex + 1 }} / {{ sampleImages.length }}
      </div>
    </div>

    <!-- Content Section -->
    <div class="px-4">
      <!-- Tags (horizontal scroll) - Read-only display -->
      <div v-if="trainingTags.length > 0" class="overflow-x-auto py-3 -mx-4 px-4 hide-scrollbar">
        <div class="flex gap-2 min-w-max">
          <TagButton
            v-for="tag in trainingTags"
            :key="tag"
            :label="tag.toUpperCase()"
            icon="🎨"
          />
        </div>
      </div>

      <!-- Title and Bookmark -->
      <div class="flex items-start justify-between py-2">
        <h1 class="text-xl font-bold text-neutral-900 flex-1 pr-4">
          {{ model.name }}
        </h1>
        <button v-if="!isOwnStyle" @click="toggleBookmark" class="p-1">
          <svg
            class="w-6 h-6 text-neutral-900"
            :fill="isBookmarked ? 'currentColor' : 'none'"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"></path>
          </svg>
        </button>
      </div>

      <!-- Description -->
      <div v-if="model.description" class="py-2">
        <p class="text-sm text-neutral-900 leading-relaxed">
          {{ model.description }}
        </p>
      </div>

      <!-- Time -->
      <div class="text-xs text-neutral-500 py-2">
        {{ formatTimeAgo(model.created_at) }}
      </div>

      <!-- Styled By (Artist) -->
      <div class="flex items-center justify-end gap-2 py-3 border-t border-neutral-100">
        <span class="text-sm italic text-neutral-900" style="font-family: 'Brush Script MT', cursive;">
          Styled by
        </span>
        <button @click="navigateToArtist" class="flex items-center gap-1.5 hover:opacity-70 transition-opacity">
          <div class="w-6 h-6 rounded-full bg-neutral-200 flex items-center justify-center overflow-hidden">
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
          <span class="text-sm font-semibold text-neutral-900">
            {{ model.artist_username || 'Unknown Artist' }}
          </span>
        </button>
      </div>

      <!-- Example Generate Image Section -->
      <div class="py-4 border-t border-neutral-100">
        <h2 class="text-base font-semibold text-neutral-900 mb-3">{{ $t('styleDetail.exampleGenerateImage') }}</h2>

        <!-- Example Image (same as training image for now) -->
        <div class="relative w-full aspect-square bg-neutral-100 mb-4 rounded-lg overflow-hidden">
          <img
            v-if="currentImage"
            :src="currentImage"
            :alt="model.name"
            class="w-full h-full object-cover"
          />

          <!-- Carousel Dots -->
          <div v-if="sampleImages.length > 1" class="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
            <button
              v-for="(image, index) in sampleImages"
              :key="`gen-${index}`"
              @click="currentImageIndex = index"
              class="w-1.5 h-1.5 rounded-full transition-colors"
              :class="currentImageIndex === index ? 'bg-white' : 'bg-white/50'"
            ></button>
          </div>
        </div>

        <!-- Warning Message (conditional) -->
        <div v-if="showWarning" class="mb-4 p-3 bg-red-50 border border-red-200 rounded-lg flex gap-3">
          <div class="flex-shrink-0">
            <svg class="w-5 h-5 text-red-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clip-rule="evenodd"></path>
            </svg>
          </div>
          <div class="flex-1">
            <h3 class="text-sm font-semibold text-red-900 mb-1">{{ $t('styleDetail.warningTitle') }}</h3>
            <p class="text-xs text-red-700">
              {{ $t('styleDetail.warningMessage') }}
            </p>
          </div>
        </div>

        <!-- User Tags (editable) - Horizontal scroll -->
        <div class="mb-4 overflow-x-auto -mx-4 px-4 hide-scrollbar">
          <div class="flex gap-2 min-w-max">
            <button
              v-for="(tag, index) in generationTags"
              :key="`tag-${index}`"
              @click="removeTag(index)"
              class="inline-flex items-center px-3 py-1.5 rounded-full border-2 text-xs font-medium transition-colors whitespace-nowrap"
              :class="index === 0
                ? 'bg-white border-neutral-300 text-neutral-700 cursor-default'
                : 'bg-white border-neutral-300 text-neutral-700 hover:border-red-300 hover:bg-red-50'"
            >
              <svg class="w-4 h-4 mr-1.5" viewBox="0 0 20 20">
                <defs>
                  <linearGradient id="tagGradient" x1="0%" y1="0%" x2="100%" y2="0%">
                    <stop offset="0%" style="stop-color:#fb923c;stop-opacity:1" />
                    <stop offset="50%" style="stop-color:#facc15;stop-opacity:1" />
                    <stop offset="100%" style="stop-color:#4ade80;stop-opacity:1" />
                  </linearGradient>
                </defs>
                <path
                  fill="url(#tagGradient)"
                  fill-rule="evenodd"
                  d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z"
                  clip-rule="evenodd"
                />
              </svg>
              {{ tag.toUpperCase() }}
            </button>
          </div>
        </div>

        <!-- Tag Input -->
        <div class="mb-3">
          <div class="relative">
            <input
              v-model="newTagInput"
              type="text"
              :placeholder="$t('styleDetail.tagInputPlaceholder')"
              :class="[
                'w-full pl-3 pr-10 py-3 border rounded-lg text-sm focus:outline-none focus:ring-2 transition-colors',
                tagError
                  ? 'border-red-500 focus:ring-red-500 bg-red-50'
                  : 'border-neutral-300 focus:ring-primary-500 focus:border-transparent'
              ]"
              @input="filterTagEnglishOnly"
              @keyup.enter="addNewTag"
            />
            <button
              @click="addNewTag"
              class="absolute right-2 top-1/2 -translate-y-1/2 p-1.5 hover:bg-neutral-100 rounded-md transition-colors"
              title="Add new tag"
            >
              <svg class="w-5 h-5 text-neutral-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 4v16m8-8H4"></path>
              </svg>
            </button>
          </div>
          <p v-if="tagError" class="text-xs text-red-600 mt-2">
            {{ $t('generation.errors.englishOnly') }}
          </p>
        </div>

        <!-- Aspect Ratio Selector -->
        <div class="mb-3 p-3 bg-neutral-50 border border-neutral-200 rounded-lg">
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="option in aspectRatioOptions"
              :key="option.value"
              @click="selectedAspectRatio = option.value"
              class="p-3 border-2 rounded-lg text-xs font-medium transition-colors flex flex-col items-center gap-2"
              :class="selectedAspectRatio === option.value
                ? 'border-primary-500 bg-primary-50 text-primary-700'
                : 'border-neutral-300 bg-white text-neutral-700 hover:border-neutral-400'"
            >
              <!-- Aspect ratio icon -->
              <div v-if="option.value === '1:1'" class="w-8 h-8 border-2 border-current rounded"></div>
              <div v-else-if="option.value === '2:2'" class="w-10 h-10 border-2 border-current rounded"></div>
              <div v-else-if="option.value === '1:2'" class="w-6 h-10 border-2 border-current rounded"></div>
              <span>{{ option.value }}</span>
            </button>
          </div>
        </div>

        <!-- Price Display -->
        <div class="mb-3 p-3 bg-gradient-to-r from-orange-50 via-yellow-50 to-green-50 border-2 border-orange-200 rounded-lg">
          <div class="flex items-center justify-between">
            <span class="text-sm font-medium text-neutral-700">{{ $t('styleDetail.generationCost') }}</span>
            <div class="flex items-center gap-1.5">
              <svg class="w-5 h-5 text-yellow-500" fill="currentColor" viewBox="0 0 20 20">
                <path d="M8.433 7.418c.155-.103.346-.196.567-.267v1.698a2.305 2.305 0 01-.567-.267C8.07 8.34 8 8.114 8 8c0-.114.07-.34.433-.582zM11 12.849v-1.698c.22.071.412.164.567.267.364.243.433.468.433.582 0 .114-.07.34-.433.582a2.305 2.305 0 01-.567.267z"></path>
                <path fill-rule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zm1-13a1 1 0 10-2 0v.092a4.535 4.535 0 00-1.676.662C6.602 6.234 6 7.009 6 8c0 .99.602 1.765 1.324 2.246.48.32 1.054.545 1.676.662v1.941c-.391-.127-.68-.317-.843-.504a1 1 0 10-1.51 1.31c.562.649 1.413 1.076 2.353 1.253V15a1 1 0 102 0v-.092a4.535 4.535 0 001.676-.662C13.398 13.766 14 12.991 14 12c0-.99-.602-1.765-1.324-2.246A4.535 4.535 0 0011 9.092V7.151c.391.127.68.317.843.504a1 1 0 101.511-1.31c-.563-.649-1.413-1.076-2.354-1.253V5z" clip-rule="evenodd"></path>
              </svg>
              <span class="text-lg font-bold text-neutral-900">{{ model.generation_cost_tokens }}</span>
              <span class="text-sm text-neutral-600">tokens</span>
            </div>
          </div>
          <p class="text-xs text-neutral-500 mt-1.5">{{ $t('styleDetail.tokensWillBeDeducted') }}</p>
        </div>

        <!-- Generate Button -->
        <button
          @click="handleGenerate"
          :disabled="!canGenerate"
          class="w-full py-3.5 rounded-lg font-semibold text-white transition-all flex items-center justify-center"
          :class="canGenerate
            ? 'bg-gradient-to-r from-orange-400 via-yellow-400 to-green-400 hover:shadow-lg'
            : 'bg-neutral-300 cursor-not-allowed'"
        >
          <span>{{ $t('styleDetail.generateButton') }}</span>
        </button>

        <!-- Helper text -->
        <p v-if="!authStore.isAuthenticated" class="text-xs text-neutral-500 text-center mt-2">
          {{ $t('styleDetail.pleaseLogin') }}
        </p>
        <p v-else-if="isGenerating" class="text-xs text-primary-600 text-center mt-2">
          {{ $t('styleDetail.generating') }}
        </p>
      </div>
    </div>
    </AppLayout>
  </div>

  <!-- Error state -->
  <div v-else class="flex flex-col items-center justify-center min-h-screen text-center px-4">
    <svg class="w-16 h-16 text-neutral-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M12 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
    </svg>
    <p class="text-neutral-500 mb-4">{{ $t('styleDetail.styleNotFound') }}</p>
    <button @click="router.back()" class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium">
      {{ $t('styleDetail.goBack') }}
    </button>
  </div>
</template>

<style scoped>
/* Hide scrollbar for horizontal scroll containers */
.hide-scrollbar::-webkit-scrollbar {
  display: none;
}

.hide-scrollbar {
  -ms-overflow-style: none;  /* IE and Edge */
  scrollbar-width: none;  /* Firefox */
}
</style>
