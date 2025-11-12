/**
 * ImagePreview Component
 *
 * Displays generated image with download and regenerate actions.
 */
<script setup>
import { ref } from 'vue'
import Button from '@/components/shared/Button.vue'
import ProgressIndicator from './ProgressIndicator.vue'

const props = defineProps({
  generation: {
    type: Object,
    required: true,
  },
  showActions: {
    type: Boolean,
    default: true,
  },
})

const emit = defineEmits(['regenerate', 'delete'])

// State
const isDownloading = ref(false)

// Download image
const handleDownload = async () => {
  if (!props.generation.image_url) return

  try {
    isDownloading.value = true

    // Fetch the image
    const response = await fetch(props.generation.image_url)
    const blob = await response.blob()

    // Create download link
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    link.download = `generation-${props.generation.id}.png`
    document.body.appendChild(link)
    link.click()

    // Cleanup
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (error) {
    console.error('Failed to download image:', error)
    alert('Failed to download image. Please try again.')
  } finally {
    isDownloading.value = false
  }
}

// Regenerate with same params
const handleRegenerate = () => {
  emit('regenerate', {
    style_id: props.generation.style_id,
    prompt: props.generation.prompt,
    aspect_ratio: props.generation.aspect_ratio,
    seed: props.generation.seed,
  })
}

// Delete generation
const handleDelete = () => {
  if (confirm('Are you sure you want to delete this generation?')) {
    emit('delete', props.generation.id)
  }
}

// Format date
const formatDate = (dateString) => {
  if (!dateString) return ''
  const date = new Date(dateString)
  return date.toLocaleDateString('en-US', {
    year: 'numeric',
    month: 'short',
    day: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  })
}
</script>

<template>
  <div class="bg-white rounded-lg shadow-md overflow-hidden">
    <!-- Image -->
    <div class="relative bg-neutral-100 aspect-square">
      <img
        v-if="generation.image_url && generation.status === 'completed'"
        :src="generation.image_url"
        :alt="`Generation ${generation.id}`"
        class="w-full h-full object-contain"
      />

      <!-- Loading State -->
      <div
        v-else-if="generation.status === 'processing' || generation.status === 'queued'"
        class="w-full h-full flex flex-col items-center justify-center"
      >
        <ProgressIndicator :status="generation.status" size="lg" />
        <p class="text-neutral-600 mt-4 text-center px-4">
          {{ generation.status === 'queued' ? 'Waiting in queue...' : 'Generating your image...' }}
        </p>
        <p class="text-neutral-500 text-sm mt-2">
          This may take a few moments
        </p>
      </div>

      <!-- Failed State -->
      <div
        v-else-if="generation.status === 'failed'"
        class="w-full h-full flex flex-col items-center justify-center p-8"
      >
        <svg class="w-16 h-16 text-red-400 mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
        </svg>
        <p class="text-neutral-900 font-semibold mb-2">Generation Failed</p>
        <p class="text-neutral-600 text-sm text-center">
          {{ generation.error_message || 'An error occurred during generation' }}
        </p>
      </div>

      <!-- Status Badge (top-right) -->
      <div
        v-if="generation.status !== 'completed'"
        class="absolute top-3 right-3"
      >
        <ProgressIndicator :status="generation.status" size="sm" />
      </div>
    </div>

    <!-- Info and Actions -->
    <div class="p-4 space-y-3">
      <!-- Metadata -->
      <div class="space-y-1">
        <!-- Prompt -->
        <div v-if="generation.prompt" class="text-sm">
          <span class="font-medium text-neutral-700">Prompt:</span>
          <span class="text-neutral-600 ml-2">{{ generation.prompt }}</span>
        </div>

        <!-- Style Model -->
        <div v-if="generation.style_model" class="text-sm">
          <span class="font-medium text-neutral-700">Style:</span>
          <span class="text-neutral-600 ml-2">{{ generation.style_model.name }}</span>
        </div>

        <!-- Aspect Ratio -->
        <div v-if="generation.aspect_ratio" class="text-sm">
          <span class="font-medium text-neutral-700">Aspect Ratio:</span>
          <span class="text-neutral-600 ml-2">{{ generation.aspect_ratio }}</span>
        </div>

        <!-- Created At -->
        <div class="text-xs text-neutral-500">
          {{ formatDate(generation.created_at) }}
        </div>
      </div>

      <!-- Action Buttons -->
      <div v-if="showActions && generation.status === 'completed'" class="flex gap-2">
        <Button
          variant="primary"
          size="sm"
          fullWidth
          :loading="isDownloading"
          @click="handleDownload"
        >
          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16v1a3 3 0 003 3h10a3 3 0 003-3v-1m-4-4l-4 4m0 0l-4-4m4 4V4" />
          </svg>
          Download
        </Button>

        <Button
          variant="outline"
          size="sm"
          @click="handleRegenerate"
        >
          <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15" />
          </svg>
          Regenerate
        </Button>

        <Button
          variant="ghost"
          size="sm"
          @click="handleDelete"
        >
          <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
          </svg>
        </Button>
      </div>

      <!-- Retry Button (for failed) -->
      <div v-else-if="showActions && generation.status === 'failed'" class="flex gap-2">
        <Button
          variant="primary"
          size="sm"
          fullWidth
          @click="handleRegenerate"
        >
          Retry
        </Button>
        <Button
          variant="outline"
          size="sm"
          @click="handleDelete"
        >
          Delete
        </Button>
      </div>
    </div>
  </div>
</template>
