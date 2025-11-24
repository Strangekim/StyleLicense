/**
 * ImageGeneration Page
 *
 * Main interface for generating images with AI style models.
 * Allows users to select style, input prompt, choose aspect ratio, and generate images.
 */
<script setup>
import { ref, computed, onMounted, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useModelsStore } from '@/stores/models'
import { useGenerationStore } from '@/stores/generations'
import { useTokenStore } from '@/stores/tokens'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/layout/AppLayout.vue'
import Input from '@/components/shared/Input.vue'
import Button from '@/components/shared/Button.vue'
import Card from '@/components/shared/Card.vue'
import ImagePreview from '@/components/features/generation/ImagePreview.vue'

const route = useRoute()
const router = useRouter()
const { t } = useI18n()
const modelsStore = useModelsStore()
const generationStore = useGenerationStore()
const tokenStore = useTokenStore()
const authStore = useAuthStore()

// Form state
const formData = ref({
  style_id: null,
  prompt: '',
  aspect_ratio: '1:1',
  seed: null,
})

// UI state
const isGenerating = ref(false)
const errors = ref({})
const availableModels = ref([])
const selectedModel = ref(null)
const promptError = ref(false) // Track non-English input attempt

// Aspect ratio options with token costs
const aspectRatioOptions = [
  { value: '1:1', label: '1:1 (512×512px)', cost: 10 },
  { value: '2:2', label: '2:2 (1024×1024px)', cost: 20 },
  { value: '1:2', label: '1:2 (512×1024px)', cost: 15 },
  { value: '2:1', label: '2:1 (1024×512px)', cost: 15 },
]

// Computed
const tokenCost = computed(() => {
  const option = aspectRatioOptions.find((opt) => opt.value === formData.value.aspect_ratio)
  return option ? option.cost : 10
})

const hasInsufficientTokens = computed(() => {
  return tokenStore.balance < tokenCost.value
})

const canGenerate = computed(() => {
  return (
    formData.value.style_id &&
    formData.value.prompt.trim() &&
    !hasInsufficientTokens.value &&
    !isGenerating.value
  )
})

const activeGenerations = computed(() => {
  return generationStore.queue
})

// Load models on mount
onMounted(async () => {
  // Fetch user balance
  if (authStore.isAuthenticated) {
    await tokenStore.fetchBalance()
  }

  // Fetch completed models
  await modelsStore.fetchModels({ training_status: 'completed' })
  availableModels.value = modelsStore.models

  // Pre-select style from query param (if coming from model detail page)
  const styleId = route.query.styleId
  if (styleId) {
    formData.value.style_id = parseInt(styleId)
    selectedModel.value = availableModels.value.find((m) => m.id === formData.value.style_id)
  }
})

// Watch style selection
watch(
  () => formData.value.style_id,
  (newStyleId) => {
    selectedModel.value = availableModels.value.find((m) => m.id === newStyleId)
  }
)

// Filter to allow only English letters and spaces
const filterEnglishOnly = (event) => {
  const input = event.target.value
  const filtered = input.replace(/[^a-zA-Z\s]/g, '')

  // Check if non-English characters were attempted
  if (input !== filtered) {
    promptError.value = true
    formData.value.prompt = filtered
    // Trigger input event to update cursor position
    event.target.value = filtered
  } else {
    promptError.value = false
  }
}

// Validate form
const validateForm = () => {
  const newErrors = {}

  if (!formData.value.style_id) {
    newErrors.style_id = t('generation.errors.selectStyle')
  }

  if (!formData.value.prompt.trim()) {
    newErrors.prompt = t('generation.errors.enterPrompt')
  }

  if (formData.value.prompt.length > 500) {
    newErrors.prompt = t('generation.errors.promptTooLong')
  }

  // Check if prompt contains only English letters and spaces
  const englishOnlyRegex = /^[a-zA-Z\s]*$/
  if (formData.value.prompt && !englishOnlyRegex.test(formData.value.prompt)) {
    newErrors.prompt = t('generation.errors.englishOnly')
  }

  errors.value = newErrors
  return Object.keys(newErrors).length === 0
}

// Generate image
const handleGenerate = async () => {
  if (!validateForm()) {
    return
  }

  if (hasInsufficientTokens.value) {
    if (confirm(t('generation.insufficientTokensConfirm'))) {
      router.push('/tokens')
    }
    return
  }

  isGenerating.value = true

  try {
    const data = {
      style_id: formData.value.style_id,
      prompt: formData.value.prompt,
      aspect_ratio: formData.value.aspect_ratio,
    }

    // Add seed if provided
    if (formData.value.seed) {
      data.seed = parseInt(formData.value.seed)
    }

    await generationStore.generateImage(data)

    // Deduct tokens optimistically
    tokenStore.updateBalance(-tokenCost.value)

    // Show success message
    alert(t('generation.generationStarted'))

    // Clear prompt for next generation
    formData.value.prompt = ''
  } catch (error) {
    console.error('Generation failed:', error)
    errors.value.submit = error.response?.data?.error?.message || t('generation.errors.generationFailed')
  } finally {
    isGenerating.value = false
  }
}

// Handle regenerate from preview
const handleRegenerate = (params) => {
  formData.value = {
    style_id: params.style_id,
    prompt: params.prompt,
    aspect_ratio: params.aspect_ratio,
    seed: params.seed,
  }

  // Scroll to top
  window.scrollTo({ top: 0, behavior: 'smooth' })
}

// Navigate to history
const viewHistory = () => {
  router.push('/generate/history')
}
</script>

<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Page Header -->
      <div class="mb-8">
        <h1 class="text-3xl font-bold text-neutral-900 mb-2">
          {{ $t('generation.title') }}
        </h1>
        <p class="text-neutral-600">
          {{ $t('generation.subtitle') }}
        </p>
      </div>

      <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
        <!-- Left Column: Generation Form -->
        <div class="lg:col-span-2 space-y-6">
          <!-- Style Selector -->
          <Card>
            <h2 class="text-xl font-semibold text-neutral-900 mb-4">
              {{ $t('generation.selectStyle') }}
            </h2>

            <div v-if="availableModels.length > 0">
              <select
                v-model="formData.style_id"
                class="w-full px-4 py-2 border border-neutral-300 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                :class="{ 'border-red-500': errors.style_id }"
              >
                <option :value="null" disabled>{{ $t('generation.chooseStyle') }}</option>
                <option v-for="model in availableModels" :key="model.id" :value="model.id">
                  {{ model.name }} by {{ model.artist?.username }}
                </option>
              </select>
              <p v-if="errors.style_id" class="text-red-600 text-sm mt-1">
                {{ errors.style_id }}
              </p>

              <!-- Selected Model Preview -->
              <div v-if="selectedModel" class="mt-4 p-3 bg-neutral-50 rounded-lg flex items-center gap-3">
                <div class="w-16 h-16 bg-neutral-200 rounded-lg overflow-hidden flex-shrink-0">
                  <img
                    v-if="selectedModel.sample_images && selectedModel.sample_images[0]"
                    :src="selectedModel.sample_images[0]"
                    :alt="selectedModel.name"
                    class="w-full h-full object-cover"
                  />
                </div>
                <div class="flex-1 min-w-0">
                  <p class="font-semibold text-neutral-900 truncate">{{ selectedModel.name }}</p>
                  <p class="text-sm text-neutral-600">by {{ selectedModel.artist?.username }}</p>
                </div>
              </div>
            </div>

            <div v-else class="text-center py-8">
              <p class="text-neutral-600">{{ $t('generation.loadingStyles') }}</p>
            </div>
          </Card>

          <!-- Prompt Input -->
          <Card>
            <h2 class="text-xl font-semibold text-neutral-900 mb-4">
              {{ $t('generation.prompt') }}
            </h2>

            <Input
              v-model="formData.prompt"
              type="textarea"
              :placeholder="$t('generation.promptPlaceholder')"
              :rows="4"
              :error="errors.prompt"
              :class="{ 'border-red-500 bg-red-50': promptError }"
              @input="filterEnglishOnly"
            >
              <template #helper>
                {{ formData.prompt.length }}/500 {{ $t('generation.characters') }}
              </template>
            </Input>

            <p v-if="promptError" class="text-xs text-red-600 mt-2">
              {{ $t('generation.errors.englishOnly') }}
            </p>
          </Card>

          <!-- Settings -->
          <Card>
            <h2 class="text-xl font-semibold text-neutral-900 mb-4">
              {{ $t('generation.settings') }}
            </h2>

            <div class="space-y-4">
              <!-- Aspect Ratio -->
              <div>
                <label class="block text-sm font-medium text-neutral-700 mb-2">
                  {{ $t('generation.aspectRatio') }}
                </label>
                <div class="grid grid-cols-2 gap-3">
                  <button
                    v-for="option in aspectRatioOptions"
                    :key="option.value"
                    type="button"
                    class="px-4 py-3 border-2 rounded-lg text-sm font-medium transition-colors"
                    :class="{
                      'border-primary-600 bg-primary-50 text-primary-700': formData.aspect_ratio === option.value,
                      'border-neutral-300 bg-white text-neutral-700 hover:border-neutral-400': formData.aspect_ratio !== option.value,
                    }"
                    @click="formData.aspect_ratio = option.value"
                  >
                    <div>{{ option.label }}</div>
                    <div class="text-xs mt-1">{{ option.cost }} {{ $t('generation.tokens') }}</div>
                  </button>
                </div>
              </div>

              <!-- Seed (Advanced) -->
              <details>
                <summary class="cursor-pointer text-sm font-medium text-neutral-700 mb-2">
                  {{ $t('generation.advancedSeed') }}
                </summary>
                <Input
                  v-model.number="formData.seed"
                  type="number"
                  :placeholder="$t('generation.seedPlaceholder')"
                  :helper="$t('generation.seedHelper')"
                />
              </details>
            </div>
          </Card>

          <!-- Generate Button -->
          <Card>
            <div class="flex items-center justify-between mb-4">
              <div>
                <p class="text-sm text-neutral-600">{{ $t('generation.cost') }}</p>
                <p class="text-2xl font-bold text-primary-600">
                  {{ tokenCost }} {{ $t('generation.tokens') }}
                </p>
              </div>
              <div class="text-right">
                <p class="text-sm text-neutral-600">{{ $t('generation.yourBalance') }}</p>
                <p
                  class="text-2xl font-bold"
                  :class="{
                    'text-green-600': !hasInsufficientTokens,
                    'text-red-600': hasInsufficientTokens,
                  }"
                >
                  {{ tokenStore.balance }} {{ $t('generation.tokens') }}
                </p>
              </div>
            </div>

            <Button
              variant="primary"
              size="lg"
              fullWidth
              :disabled="!canGenerate"
              :loading="isGenerating"
              @click="handleGenerate"
            >
              {{ hasInsufficientTokens ? $t('generation.insufficientTokens') : $t('generation.generate') }}
            </Button>

            <p v-if="hasInsufficientTokens" class="text-center text-sm text-red-600 mt-2">
              <router-link to="/tokens" class="underline hover:text-red-700">
                {{ $t('generation.purchaseMoreTokens') }}
              </router-link>
            </p>

            <p v-if="errors.submit" class="text-red-600 text-sm mt-2">
              {{ errors.submit }}
            </p>
          </Card>
        </div>

        <!-- Right Column: Active Generations -->
        <div class="space-y-6">
          <div class="flex items-center justify-between">
            <h2 class="text-xl font-semibold text-neutral-900">
              {{ $t('generation.activeGenerations') }}
            </h2>
            <Button variant="ghost" size="sm" @click="viewHistory">
              {{ $t('generation.viewHistory') }}
            </Button>
          </div>

          <!-- Active Generation Queue -->
          <div v-if="activeGenerations.length > 0" class="space-y-4">
            <ImagePreview
              v-for="generation in activeGenerations"
              :key="generation.id"
              :generation="generation"
              :show-actions="false"
            />
          </div>

          <!-- Empty State -->
          <Card v-else>
            <div class="text-center py-8">
              <svg class="w-16 h-16 text-neutral-400 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <p class="text-neutral-600">
                {{ $t('generation.noActiveGenerations') }}
              </p>
              <p class="text-neutral-500 text-sm mt-1">
                {{ $t('generation.startGenerating') }}
              </p>
            </div>
          </Card>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
