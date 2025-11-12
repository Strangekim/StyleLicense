/**
 * ModelCard Component
 *
 * Displays a style model card with thumbnail, name, artist, and tags.
 * Used in marketplace grid and artist profile pages.
 */
<script setup>
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import Card from '@/components/shared/Card.vue'

const props = defineProps({
  model: {
    type: Object,
    required: true,
  },
})

const router = useRouter()

// Get first sample image or placeholder
const thumbnailUrl = computed(() => {
  if (props.model.sample_images && props.model.sample_images.length > 0) {
    return props.model.sample_images[0]
  }
  return null // Placeholder can be added later
})

// Format training status
const statusLabel = computed(() => {
  const statusMap = {
    'pending': 'Training Pending',
    'training': 'Training...',
    'completed': 'Ready',
    'failed': 'Training Failed',
  }
  return statusMap[props.model.training_status] || 'Unknown'
})

const statusColor = computed(() => {
  const colorMap = {
    'pending': 'text-yellow-600 bg-yellow-50',
    'training': 'text-blue-600 bg-blue-50',
    'completed': 'text-green-600 bg-green-50',
    'failed': 'text-red-600 bg-red-50',
  }
  return colorMap[props.model.training_status] || 'text-neutral-600 bg-neutral-50'
})

const handleClick = () => {
  router.push(`/models/${props.model.id}`)
}
</script>

<template>
  <Card
    clickable
    variant="elevated"
    padding="none"
    class="overflow-hidden"
    @click="handleClick"
  >
    <!-- Thumbnail -->
    <div class="aspect-square bg-neutral-100 relative overflow-hidden">
      <img
        v-if="thumbnailUrl"
        :src="thumbnailUrl"
        :alt="model.name"
        class="w-full h-full object-cover transition-transform duration-300 hover:scale-110"
      />
      <div
        v-else
        class="w-full h-full flex items-center justify-center text-neutral-400"
      >
        <svg
          class="w-16 h-16"
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
      </div>

      <!-- Status Badge (if not completed) -->
      <div
        v-if="model.training_status !== 'completed'"
        class="absolute top-2 right-2"
      >
        <span
          :class="[
            'px-2 py-1 rounded-full text-xs font-medium',
            statusColor,
          ]"
        >
          {{ statusLabel }}
        </span>
      </div>
    </div>

    <!-- Content -->
    <div class="p-4">
      <!-- Model Name -->
      <h3 class="font-semibold text-neutral-900 text-lg mb-1 truncate">
        {{ model.name }}
      </h3>

      <!-- Artist Name -->
      <p class="text-sm text-neutral-600 mb-3 truncate">
        by {{ model.artist?.username || 'Unknown Artist' }}
      </p>

      <!-- Tags (max 3 shown) -->
      <div v-if="model.tags && model.tags.length > 0" class="flex flex-wrap gap-1 mb-3">
        <span
          v-for="tag in model.tags.slice(0, 3)"
          :key="tag.id || tag.name"
          class="px-2 py-1 bg-neutral-100 text-neutral-700 rounded-full text-xs"
        >
          {{ tag.name || tag }}
        </span>
        <span
          v-if="model.tags.length > 3"
          class="px-2 py-1 bg-neutral-100 text-neutral-500 rounded-full text-xs"
        >
          +{{ model.tags.length - 3 }}
        </span>
      </div>

      <!-- Stats -->
      <div class="flex items-center justify-between text-sm text-neutral-600">
        <div class="flex items-center gap-3">
          <!-- Usage Count -->
          <div class="flex items-center gap-1">
            <svg
              class="w-4 h-4"
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
            <span>{{ model.usage_count || 0 }}</span>
          </div>
        </div>

        <!-- Price -->
        <div class="font-semibold text-primary-600">
          {{ model.price_per_generation || 10 }} tokens
        </div>
      </div>
    </div>
  </Card>
</template>
