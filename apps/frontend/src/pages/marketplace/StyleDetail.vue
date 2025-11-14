/**
 * StyleDetail Page (Unified Model Detail + Generation)
 *
 * Based on StyleDetailPage1-4 mockups
 * Combines style information viewing and image generation in a single scrollable page
 */
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useModelsStore } from '@/stores/models'
import { useGenerationStore } from '@/stores/generations'
import { useTokenStore } from '@/stores/tokens'
import { useAuthStore } from '@/stores/auth'
import TagButton from '@/components/shared/TagButton.vue'

const route = useRoute()
const router = useRouter()
const modelsStore = useModelsStore()
const generationStore = useGenerationStore()
const tokenStore = useTokenStore()
const authStore = useAuthStore()

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
const showAspectRatioSelector = ref(false)
const selectedAspectRatio = ref('1:1') // Default aspect ratio

// Aspect ratio options
const aspectRatioOptions = [
  { value: '1:1', icon: 'square' },
  { value: '2:2', icon: 'square-large' },
  { value: '1:2', icon: 'portrait' },
]

// Computed
const sampleImages = computed(() => {
  return model.value?.sample_images || []
})

const currentImage = computed(() => {
  return sampleImages.value[currentImageIndex.value] || null
})

// All tags to display: default tag (style name) + user tags
const allTags = computed(() => {
  const defaultTag = model.value?.name || 'STYLE'
  return [defaultTag, ...userTags.value]
})

const canGenerate = computed(() => {
  return (
    model.value?.training_status === 'completed' &&
    allTags.value.length > 0 &&
    !isGenerating.value &&
    authStore.isAuthenticated
  )
})

// Format time ago
const formatTimeAgo = (dateString) => {
  const date = new Date(dateString)
  const now = new Date()
  const seconds = Math.floor((now - date) / 1000)

  if (seconds < 60) return 'Just now'
  if (seconds < 3600) return `${Math.floor(seconds / 60)} minutes ago`
  if (seconds < 86400) return `${Math.floor(seconds / 3600)} hours ago`
  if (seconds < 604800) return `${Math.floor(seconds / 86400)} days ago`
  return `${Math.floor(seconds / 604800)} weeks ago`
}

// Actions
const toggleBookmark = () => {
  if (!authStore.isAuthenticated) {
    router.push(`/login?returnUrl=/models/${modelId.value}`)
    return
  }
  isBookmarked.value = !isBookmarked.value
  // TODO: Call API to bookmark/unbookmark
}

const addNewTag = () => {
  const tagText = newTagInput.value.trim()
  if (!tagText) return

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

  // Clear input
  newTagInput.value = ''
}

const removeTag = (index) => {
  // Can't remove the first tag (style name)
  if (index === 0) return
  userTags.value.splice(index - 1, 1) // -1 because first tag is default
}

const toggleAspectRatioSelector = () => {
  showAspectRatioSelector.value = !showAspectRatioSelector.value
}

const selectAspectRatio = (ratio) => {
  selectedAspectRatio.value = ratio
  showAspectRatioSelector.value = false
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
    // Combine all tags as the prompt
    const combinedPrompt = allTags.value.join(', ')

    const data = {
      style_id: modelId.value,
      prompt: combinedPrompt,
      aspect_ratio: selectedAspectRatio.value,
    }

    await generationStore.generateImage(data)

    // Deduct tokens
    await tokenStore.fetchBalance()

    // Show success
    alert('Image generation started! Check your generation history.')

    // Clear user tags (keep default tag)
    userTags.value = []
  } catch (error) {
    console.error('Generation failed:', error)
    alert(error.response?.data?.error?.message || 'Failed to start generation')
  } finally {
    isGenerating.value = false
  }
}

const navigateToArtist = () => {
  if (model.value?.artist?.id) {
    router.push(`/artist/${model.value.artist.id}`)
  }
}

// Fetch model on mount
onMounted(async () => {
  try {
    await modelsStore.fetchModelDetail(modelId.value)

    // Fetch user balance if authenticated
    if (authStore.isAuthenticated) {
      await tokenStore.fetchBalance()
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

  <div v-else-if="model" class="min-h-screen bg-white pb-20">
    <!-- Training Image Section -->
    <div class="px-4 pt-3 pb-2">
      <h2 class="text-base font-semibold text-neutral-900">Training Image</h2>
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

      <!-- Carousel Dots -->
      <div v-if="sampleImages.length > 1" class="absolute bottom-3 left-1/2 -translate-x-1/2 flex gap-1.5">
        <button
          v-for="(image, index) in sampleImages"
          :key="index"
          @click="currentImageIndex = index"
          class="w-1.5 h-1.5 rounded-full transition-colors"
          :class="currentImageIndex === index ? 'bg-white' : 'bg-white/50'"
        ></button>
      </div>
    </div>

    <!-- Content Section -->
    <div class="px-4">
      <!-- Tags (horizontal scroll) - Read-only display -->
      <div v-if="allTags.length > 0" class="overflow-x-auto py-3 -mx-4 px-4">
        <div class="flex gap-2 min-w-max">
          <TagButton
            v-for="tag in allTags"
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
        <button @click="toggleBookmark" class="p-1">
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

      <!-- Subtitle -->
      <p class="text-sm text-neutral-600 py-1">
        This is my new Artistic Style
      </p>

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
      <div class="flex items-center gap-2 py-3 border-t border-neutral-100">
        <span class="text-sm italic text-neutral-900" style="font-family: 'Brush Script MT', cursive;">
          Styled by
        </span>
        <button @click="navigateToArtist" class="flex items-center gap-1.5 hover:opacity-70 transition-opacity">
          <div class="w-6 h-6 rounded-full bg-neutral-200 flex items-center justify-center overflow-hidden">
            <span class="text-xs font-semibold text-neutral-700">
              {{ model.artist?.username?.charAt(0).toUpperCase() || 'A' }}
            </span>
          </div>
          <span class="text-sm font-semibold text-neutral-900">
            {{ model.artist?.username || 'Unknown Artist' }}
          </span>
        </button>
      </div>

      <!-- Example Generate Image Section -->
      <div class="py-4 border-t border-neutral-100">
        <h2 class="text-base font-semibold text-neutral-900 mb-3">Example Generate Image</h2>

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
            <h3 class="text-sm font-semibold text-red-900 mb-1">Do not Write Like These Tag</h3>
            <p class="text-xs text-red-700">
              Avoid using Irrelevant, inappropriate, or misleading words when adding tags or descriptions
            </p>
          </div>
        </div>

        <!-- User Tags (editable) -->
        <div class="mb-4">
          <div class="flex flex-wrap gap-2">
            <button
              v-for="(tag, index) in allTags"
              :key="`tag-${index}`"
              @click="removeTag(index)"
              class="px-3 py-1.5 rounded-full border-2 text-xs font-medium transition-colors"
              :class="index === 0
                ? 'bg-white border-neutral-300 text-neutral-700 cursor-default'
                : 'bg-white border-neutral-300 text-neutral-700 hover:border-red-300 hover:bg-red-50'"
            >
              <span class="mr-1">🎨</span>
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
              placeholder="write create img prompt"
              class="w-full pl-3 pr-10 py-3 border border-neutral-300 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
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
        </div>

        <!-- Aspect Ratio Selector (conditional) -->
        <div v-if="showAspectRatioSelector" class="mb-3 p-3 bg-neutral-50 border border-neutral-200 rounded-lg">
          <div class="grid grid-cols-3 gap-2">
            <button
              v-for="option in aspectRatioOptions"
              :key="option.value"
              @click="selectAspectRatio(option.value)"
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

        <!-- Generate Button -->
        <button
          @click="handleGenerate"
          :disabled="!canGenerate"
          class="w-full py-3.5 rounded-lg font-semibold text-white transition-all flex items-center justify-center gap-2"
          :class="canGenerate
            ? 'bg-gradient-to-r from-orange-400 via-yellow-400 to-green-400 hover:shadow-lg'
            : 'bg-neutral-300 cursor-not-allowed'"
        >
          <span>Image Generate</span>
          <button
            @click.stop="toggleAspectRatioSelector"
            class="flex items-center gap-1 px-2 py-1 bg-white/20 rounded hover:bg-white/30 transition-colors"
          >
            <!-- Aspect ratio icons -->
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 20 20">
              <rect x="3" y="3" width="14" height="14" rx="2" stroke-width="1.5"/>
            </svg>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 20 20">
              <rect x="3" y="5" width="14" height="10" rx="2" stroke-width="1.5"/>
            </svg>
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 20 20">
              <rect x="5" y="3" width="10" height="14" rx="2" stroke-width="1.5"/>
            </svg>
            <!-- Settings icon -->
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6V4m0 2a2 2 0 100 4m0-4a2 2 0 110 4m-6 8a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4m6 6v10m6-2a2 2 0 100-4m0 4a2 2 0 110-4m0 4v2m0-6V4"></path>
            </svg>
          </button>
        </button>

        <!-- Helper text -->
        <p v-if="!authStore.isAuthenticated" class="text-xs text-neutral-500 text-center mt-2">
          Please login to generate images
        </p>
        <p v-else-if="isGenerating" class="text-xs text-primary-600 text-center mt-2">
          Generating...
        </p>
      </div>
    </div>
  </div>

  <!-- Error state -->
  <div v-else class="flex flex-col items-center justify-center min-h-screen text-center px-4">
    <svg class="w-16 h-16 text-neutral-300 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M9.172 16.172a4 4 0 015.656 0M9 10h.01M15 10h.01M12 12h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"></path>
    </svg>
    <p class="text-neutral-500 mb-4">Style not found</p>
    <button @click="router.back()" class="px-4 py-2 bg-primary-500 text-white rounded-lg text-sm font-medium">
      Go Back
    </button>
  </div>
</template>
