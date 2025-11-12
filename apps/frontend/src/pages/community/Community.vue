<script setup>
import { onMounted, ref, onUnmounted } from 'vue'
import { useCommunityStore } from '@/stores/community'
import FeedItem from '@/components/features/FeedItem.vue'

const communityStore = useCommunityStore()
const observer = ref(null)
const loadMoreTrigger = ref(null)

onMounted(async () => {
  // Load initial feed
  await communityStore.fetchFeed()

  // Setup infinite scroll
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
</script>

<template>
  <div class="min-h-screen bg-neutral-50">
    <div class="container mx-auto px-4 py-8">
      <h1 class="text-3xl font-bold text-neutral-900 mb-8">Community Feed</h1>

      <!-- Feed Grid -->
      <div v-if="communityStore.feed.length > 0" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
        <FeedItem v-for="item in communityStore.feed" :key="item.id" :item="item" />
      </div>

      <!-- Loading State -->
      <div v-if="communityStore.loading && communityStore.feed.length === 0" class="flex justify-center items-center py-12">
        <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600"></div>
      </div>

      <!-- Empty State -->
      <div v-if="!communityStore.loading && communityStore.feed.length === 0" class="text-center py-12">
        <p class="text-neutral-500">No generations yet. Be the first to share!</p>
      </div>

      <!-- Load More Trigger -->
      <div ref="loadMoreTrigger" class="py-8 flex justify-center">
        <div v-if="communityStore.loading && communityStore.feed.length > 0" class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
      </div>
    </div>
  </div>
</template>
