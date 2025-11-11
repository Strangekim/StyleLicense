/**
 * ModelDetail Page
 *
 * Displays detailed information about a style model including artist info,
 * sample images, and action buttons.
 */
<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useModelsStore } from '@/stores/models'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/layout/AppLayout.vue'
import Button from '@/components/shared/Button.vue'
import Card from '@/components/shared/Card.vue'

const route = useRoute()
const router = useRouter()
const modelsStore = useModelsStore()
const authStore = useAuthStore()

// State
const modelId = computed(() => parseInt(route.params.id))
const model = computed(() => modelsStore.currentModel)
const isLoading = computed(() => modelsStore.loading)
const error = computed(() => modelsStore.error)

const selectedImage = ref(null) // For gallery lightbox (optional feature)

// Computed
const isOwner = computed(() => {
  return authStore.user && model.value && model.value.artist?.id === authStore.user.id
})

const canGenerate = computed(() => {
  return model.value && model.value.training_status === 'completed'
})

// Actions
const handleGenerate = () => {
  if (!authStore.isAuthenticated) {
    router.push(`/login?returnUrl=/generate?styleId=${modelId.value}`)
    return
  }
  router.push({
    path: '/generate',
    query: { styleId: modelId.value }
  })
}

const handleEdit = () => {
  // Navigate to edit page (if implemented)
  router.push(`/styles/${modelId.value}/edit`)
}

const handleDelete = async () => {
  if (confirm('Are you sure you want to delete this style? This action cannot be undone.')) {
    try {
      await modelsStore.deleteModel(modelId.value)
      router.push('/marketplace')
    } catch (err) {
      console.error('Failed to delete model:', err)
    }
  }
}

// Fetch model on mount
onMounted(async () => {
  try {
    await modelsStore.fetchModelDetail(modelId.value)
  } catch (err) {
    console.error('Failed to fetch model detail:', err)
  }
})

// Format date
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'long',
    day: 'numeric'
  })
}
</script>

<template>
  <AppLayout>
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <!-- Loading State -->
      <div v-if="isLoading && !model" class="animate-pulse space-y-8">
        <div class="h-8 bg-neutral-200 rounded w-1/3"></div>
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <div class="aspect-square bg-neutral-200 rounded-lg"></div>
          <div class="space-y-4">
            <div class="h-6 bg-neutral-200 rounded"></div>
            <div class="h-4 bg-neutral-200 rounded"></div>
            <div class="h-4 bg-neutral-200 rounded w-2/3"></div>
          </div>
        </div>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="text-center py-16">
        <svg
          class="w-16 h-16 text-red-400 mx-auto mb-4"
          fill="none"
          stroke="currentColor"
          viewBox="0 0 24 24"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
          />
        </svg>
        <h3 class="text-lg font-semibold text-neutral-900 mb-2">
          Failed to load style
        </h3>
        <p class="text-neutral-600 mb-4">{{ error }}</p>
        <Button variant="outline" @click="router.push('/marketplace')">
          Back to Marketplace
        </Button>
      </div>

      <!-- Model Content -->
      <div v-else-if="model" class="space-y-8">
        <!-- Back Button -->
        <Button
          variant="ghost"
          size="sm"
          @click="router.push('/marketplace')"
        >
          <svg class="w-5 h-5 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
          Back to Marketplace
        </Button>

        <!-- Main Content Grid -->
        <div class="grid grid-cols-1 lg:grid-cols-2 gap-8">
          <!-- Left Column: Image Gallery -->
          <div class="space-y-4">
            <!-- Main Image -->
            <div class="aspect-square bg-neutral-100 rounded-lg overflow-hidden">
              <img
                v-if="model.sample_images && model.sample_images.length > 0"
                :src="model.sample_images[0]"
                :alt="model.name"
                class="w-full h-full object-cover"
              />
              <div
                v-else
                class="w-full h-full flex items-center justify-center text-neutral-400"
              >
                <svg class="w-16 h-16" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
                </svg>
              </div>
            </div>

            <!-- Thumbnail Grid -->
            <div
              v-if="model.sample_images && model.sample_images.length > 1"
              class="grid grid-cols-4 gap-2"
            >
              <button
                v-for="(image, index) in model.sample_images.slice(0, 4)"
                :key="index"
                class="aspect-square bg-neutral-100 rounded-lg overflow-hidden hover:ring-2 hover:ring-primary-500 transition-all"
              >
                <img
                  :src="image"
                  :alt="`${model.name} sample ${index + 1}`"
                  class="w-full h-full object-cover"
                />
              </button>
            </div>
          </div>

          <!-- Right Column: Model Info -->
          <div class="space-y-6">
            <!-- Model Name and Status -->
            <div>
              <div class="flex items-start justify-between mb-2">
                <h1 class="text-3xl font-bold text-neutral-900">
                  {{ model.name }}
                </h1>
                <span
                  v-if="model.training_status !== 'completed'"
                  class="px-3 py-1 rounded-full text-sm font-medium"
                  :class="{
                    'bg-yellow-50 text-yellow-700': model.training_status === 'pending',
                    'bg-blue-50 text-blue-700': model.training_status === 'training',
                    'bg-red-50 text-red-700': model.training_status === 'failed',
                  }"
                >
                  {{ model.training_status }}
                </span>
              </div>
              <p v-if="model.description" class="text-neutral-600 leading-relaxed">
                {{ model.description }}
              </p>
            </div>

            <!-- Artist Info -->
            <Card padding="md">
              <div class="flex items-center gap-4">
                <div class="w-12 h-12 rounded-full bg-primary-100 flex items-center justify-center text-primary-600 font-semibold text-lg">
                  {{ model.artist?.username?.charAt(0).toUpperCase() || 'A' }}
                </div>
                <div class="flex-1">
                  <p class="text-sm text-neutral-600">Created by</p>
                  <p class="font-semibold text-neutral-900">
                    {{ model.artist?.username || 'Unknown Artist' }}
                  </p>
                </div>
                <Button
                  v-if="!isOwner && authStore.isAuthenticated"
                  variant="outline"
                  size="sm"
                >
                  Follow
                </Button>
              </div>
            </Card>

            <!-- Tags -->
            <div v-if="model.tags && model.tags.length > 0">
              <h3 class="text-sm font-semibold text-neutral-700 mb-2">Tags</h3>
              <div class="flex flex-wrap gap-2">
                <span
                  v-for="tag in model.tags"
                  :key="tag.id || tag.name"
                  class="px-3 py-1 bg-neutral-100 text-neutral-700 rounded-full text-sm"
                >
                  {{ tag.name || tag }}
                </span>
              </div>
            </div>

            <!-- Stats -->
            <div class="grid grid-cols-2 gap-4">
              <Card padding="md">
                <p class="text-sm text-neutral-600 mb-1">Usage Count</p>
                <p class="text-2xl font-bold text-neutral-900">
                  {{ model.usage_count || 0 }}
                </p>
              </Card>
              <Card padding="md">
                <p class="text-sm text-neutral-600 mb-1">Price per Generation</p>
                <p class="text-2xl font-bold text-primary-600">
                  {{ model.price_per_generation || 10 }} tokens
                </p>
              </Card>
            </div>

            <!-- Created Date -->
            <div class="text-sm text-neutral-600">
              Created on {{ formatDate(model.created_at) }}
            </div>

            <!-- Action Buttons -->
            <div class="flex gap-3">
              <Button
                v-if="canGenerate && !isOwner"
                variant="primary"
                size="lg"
                fullWidth
                @click="handleGenerate"
              >
                Generate with this Style
              </Button>

              <!-- Owner Actions -->
              <template v-if="isOwner">
                <Button
                  variant="primary"
                  size="lg"
                  fullWidth
                  @click="handleGenerate"
                >
                  Generate Image
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  @click="handleEdit"
                >
                  Edit
                </Button>
                <Button
                  variant="outline"
                  size="lg"
                  @click="handleDelete"
                >
                  Delete
                </Button>
              </template>

              <!-- Not Ready State -->
              <Button
                v-if="!canGenerate"
                variant="outline"
                size="lg"
                fullWidth
                disabled
              >
                Training in Progress
              </Button>
            </div>
          </div>
        </div>
      </div>
    </div>
  </AppLayout>
</template>
