<script setup>
import { onMounted, ref, computed, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useCommunityStore } from '@/stores/community'
import AppLayout from '@/components/layout/AppLayout.vue'

const router = useRouter()
const communityStore = useCommunityStore()

const observer = ref(null)
const loadMoreTrigger = ref(null)

// Separate feed into left and right columns
const leftColumnItems = computed(() =>
  communityStore.feed.filter((_, index) => index % 2 === 0)
)

const rightColumnItems = computed(() =>
  communityStore.feed.filter((_, index) => index % 2 === 1)
)

onMounted(async () => {
  console.log('Community page mounted')
  await communityStore.fetchFeed()
  setupInfiniteScroll()
})

onUnmounted(() => {
  if (observer.value) {
    observer.value.disconnect()
  }
})

function setupInfiniteScroll() {
  observer.value = new IntersectionObserver(
    (entries) => {
      if (entries[0].isIntersecting && communityStore.hasMore && !communityStore.loading) {
        communityStore.fetchNextPage()
      }
    },
    { threshold: 0.1 }
  )

  if (loadMoreTrigger.value) {
    observer.value.observe(loadMoreTrigger.value)
  }
}

function handleImageClick(item) {
  console.log('Image clicked:', item.id)
  router.push(`/community/${item.id}`)
}
</script>

<template>
  <div class="min-h-screen bg-white">
    <AppLayout>
      <!-- Loading State -->
      <div v-if="communityStore.loading && communityStore.feed.length === 0" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>

      <!-- Empty State -->
      <div v-else-if="!communityStore.loading && communityStore.feed.length === 0" class="text-center py-12">
        <p class="text-gray-500">No generations yet. Be the first to share!</p>
      </div>

      <!-- Masonry Grid (2 columns) - No horizontal padding -->
      <div v-else class="max-w-screen-sm mx-auto">
        <div class="grid grid-cols-2 gap-1">
          <!-- Left Column -->
          <div class="space-y-1">
            <div
              v-for="item in leftColumnItems"
              :key="item.id"
              @click="handleImageClick(item)"
              class="relative cursor-pointer overflow-hidden group bg-gray-100"
            >
              <img
                :src="item.result_url"
                :alt="item.description || 'Generated image'"
                class="w-full object-cover"
                loading="lazy"
              />
              <!-- Bookmark icon -->
              <button
                @click.stop="console.log('Bookmark clicked', item.id)"
                class="absolute top-2 right-2 bg-white bg-opacity-80 p-1.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <svg class="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              </button>
            </div>
          </div>

          <!-- Right Column -->
          <div class="space-y-1">
            <div
              v-for="item in rightColumnItems"
              :key="item.id"
              @click="handleImageClick(item)"
              class="relative cursor-pointer overflow-hidden group bg-gray-100"
            >
              <img
                :src="item.result_url"
                :alt="item.description || 'Generated image'"
                class="w-full object-cover"
                loading="lazy"
              />
              <!-- Bookmark icon -->
              <button
                @click.stop="console.log('Bookmark clicked', item.id)"
                class="absolute top-2 right-2 bg-white bg-opacity-80 p-1.5 rounded-full opacity-0 group-hover:opacity-100 transition-opacity"
              >
                <svg class="w-4 h-4 text-gray-700" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z" />
                </svg>
              </button>
            </div>
          </div>
        </div>

        <!-- Load More Trigger -->
        <div ref="loadMoreTrigger" class="py-8 flex justify-center">
          <div v-if="communityStore.loading && communityStore.feed.length > 0" class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
        </div>
      </div>
    </AppLayout>
  </div>
</template>
