<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import AppLayout from '@/components/layout/AppLayout.vue'

const router = useRouter()

// Mock data for testing
const feedItems = ref([
  { id: 1, image: 'https://picsum.photos/400/600?random=1', height: 'h-80' },
  { id: 2, image: 'https://picsum.photos/400/400?random=2', height: 'h-64' },
  { id: 3, image: 'https://picsum.photos/400/500?random=3', height: 'h-72' },
  { id: 4, image: 'https://picsum.photos/400/450?random=4', height: 'h-68' },
  { id: 5, image: 'https://picsum.photos/400/550?random=5', height: 'h-76' },
  { id: 6, image: 'https://picsum.photos/400/400?random=6', height: 'h-64' },
  { id: 7, image: 'https://picsum.photos/400/600?random=7', height: 'h-80' },
  { id: 8, image: 'https://picsum.photos/400/450?random=8', height: 'h-68' },
  { id: 9, image: 'https://picsum.photos/400/500?random=9', height: 'h-72' },
  { id: 10, image: 'https://picsum.photos/400/550?random=10', height: 'h-76' },
])

const loading = ref(false)

onMounted(() => {
  console.log('Community page mounted successfully')
})

function handleImageClick(item) {
  console.log('Image clicked:', item.id)
  router.push(`/community/${item.id}`)
}
</script>

<template>
  <div class="min-h-screen bg-white">
    <AppLayout>
      <!-- Loading State -->
      <div v-if="loading" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <!-- Masonry Grid (2 columns) -->
      <div v-else class="max-w-screen-sm mx-auto px-2 py-4">
        <div class="grid grid-cols-2 gap-2">
          <!-- Left Column -->
          <div class="space-y-2">
            <div
              v-for="(item, index) in feedItems.filter((_, i) => i % 2 === 0)"
              :key="item.id"
              @click="handleImageClick(item)"
              class="relative cursor-pointer rounded-lg overflow-hidden group"
            >
              <img
                :src="item.image"
                :alt="`Feed item ${item.id}`"
                class="w-full object-cover"
                :class="item.height"
              />
              <!-- Bookmark icon -->
              <button
                @click.stop="console.log('Bookmark clicked')"
                class="absolute top-2 right-2 bg-white bg-opacity-80 p-1.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <svg class="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Right Column -->
          <div class="space-y-2">
            <div
              v-for="(item, index) in feedItems.filter((_, i) => i % 2 === 1)"
              :key="item.id"
              @click="handleImageClick(item)"
              class="relative cursor-pointer rounded-lg overflow-hidden group"
            >
              <img
                :src="item.image"
                :alt="`Feed item ${item.id}`"
                class="w-full object-cover"
                :class="item.height"
              />
              <!-- Bookmark icon -->
              <button
                @click.stop="console.log('Bookmark clicked')"
                class="absolute top-2 right-2 bg-white bg-opacity-80 p-1.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <svg class="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  </div>
</template>
