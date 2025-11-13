<script setup>
import { ref } from 'vue'
import { useCommunityStore } from '@/stores/community'
import { formatDistanceToNow } from '@/utils/date'

const props = defineProps({
  item: {
    type: Object,
    required: true,
  },
})

const communityStore = useCommunityStore()
const isLiking = ref(false)

async function handleLike() {
  if (isLiking.value) return

  isLiking.value = true
  try {
    await communityStore.toggleLike(props.item.id)
  } catch (error) {
    console.error('Failed to toggle like:', error)
  } finally {
    isLiking.value = false
  }
}
</script>

<template>
  <router-link
    :to="`/community/${item.id}`"
    class="block bg-white rounded-lg border border-neutral-200 hover:shadow-md transition-shadow overflow-hidden"
  >
    <!-- Image -->
    <div class="aspect-square bg-neutral-100 relative">
      <img
        v-if="item.result_url"
        :src="item.result_url"
        :alt="item.description || 'Generated image'"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center text-neutral-400">
        <span class="text-4xl">🎨</span>
      </div>
    </div>

    <!-- Content -->
    <div class="p-4">
      <!-- User Info -->
      <div class="flex items-center gap-2 mb-2">
        <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
          <span class="text-sm font-semibold text-primary-700">
            {{ item.user.username.charAt(0).toUpperCase() }}
          </span>
        </div>
        <div class="flex-1 min-w-0">
          <p class="text-sm font-medium text-neutral-900 truncate">{{ item.user.username }}</p>
          <p class="text-xs text-neutral-500">{{ formatDistanceToNow(item.created_at) }}</p>
        </div>
      </div>

      <!-- Description -->
      <p v-if="item.description" class="text-sm text-neutral-700 mb-3 line-clamp-2">
        {{ item.description }}
      </p>

      <!-- Actions -->
      <div class="flex items-center gap-4 text-sm">
        <button
          @click.prevent="handleLike"
          class="flex items-center gap-1.5 transition-colors"
          :class="item.is_liked_by_current_user ? 'text-red-500' : 'text-neutral-600 hover:text-red-500'"
          :disabled="isLiking"
        >
          <svg
            class="w-5 h-5 transition-transform"
            :class="{ 'scale-110': isLiking }"
            :fill="item.is_liked_by_current_user ? 'currentColor' : 'none'"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"
            />
          </svg>
          <span>{{ item.like_count }}</span>
        </button>

        <div class="flex items-center gap-1.5 text-neutral-600">
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
            />
          </svg>
          <span>{{ item.comment_count }}</span>
        </div>
      </div>

      <!-- Style Tag -->
      <div v-if="item.style" class="mt-3 pt-3 border-t border-neutral-100">
        <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium bg-primary-50 text-primary-700">
          {{ item.style.name }}
        </span>
      </div>
    </div>
  </router-link>
</template>
