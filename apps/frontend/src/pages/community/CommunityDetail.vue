<template>
  <div class="min-h-screen bg-gray-50 pb-16">
    <!-- Custom Header -->
    <header class="sticky top-0 z-40 bg-white border-b border-gray-200">
      <div class="max-w-screen-sm mx-auto px-4 h-14 flex items-center justify-between">
        <!-- Back Button (only <) -->
        <button
          @click="handleBack"
          class="text-gray-900 hover:text-gray-600 transition-colors"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 19l-7-7 7-7" />
          </svg>
        </button>

        <!-- Empty space for balance -->
        <div class="w-6"></div>
      </div>
    </header>

    <!-- Loading State -->
    <div v-if="loading" class="flex justify-center items-center min-h-screen">
      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="max-w-2xl mx-auto px-4 py-12">
      <div class="bg-red-50 text-red-800 p-4 rounded-lg">
        {{ error }}
      </div>
      <router-link
        to="/community"
        class="mt-4 inline-block text-blue-600 hover:text-blue-700"
      >
        ← {{ $t('communityDetail.backToCommunity') }}
      </router-link>
    </div>

    <!-- Feed Detail Content -->
    <div v-else-if="feedItem" class="max-w-2xl mx-auto py-4">
      <!-- Author Info (moved from Back button location) -->
      <div class="mb-4 px-4 flex items-center space-x-2">
        <!-- Avatar -->
        <img
          :src="feedItem.user.avatar || '/default-avatar.png'"
          :alt="feedItem.user.username"
          class="w-10 h-10 rounded-full object-cover"
        />
        <!-- Username -->
        <router-link
          :to="`/profile/${feedItem.user.id}`"
          class="font-semibold text-gray-900 hover:text-blue-600"
        >
          {{ feedItem.user.username }}
        </router-link>
        <!-- Brush Icon (if author is artist) -->
        <img
          v-if="isAuthorArtist"
          :src="brushIcon"
          alt="Artist"
          class="w-5 h-5"
        />
      </div>

        <!-- Main Image -->
        <div class="bg-white rounded-lg overflow-hidden shadow-sm mb-4">
          <div class="relative">
            <!-- Image -->
            <img
              v-if="feedItem.result_url"
              :src="feedItem.result_url"
              :alt="feedItem.description || 'Generated image'"
              class="w-full object-contain"
              style="max-height: 70vh"
            />
            <div v-else class="w-full aspect-square bg-gray-100 flex items-center justify-center">
              <span class="text-6xl">🎨</span>
            </div>
          </div>

          <!-- Image Footer -->
          <div class="px-4 py-3 flex items-center justify-between border-t border-gray-100">
            <!-- Bookmark Button -->
            <button
              @click="handleBookmark"
              :disabled="bookmarking"
              class="transition-colors"
              :class="feedItem.is_bookmarked ? 'text-gray-900' : 'text-gray-400 hover:text-gray-600'"
            >
              <svg
                class="w-6 h-6"
                :fill="feedItem.is_bookmarked ? 'currentColor' : 'none'"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M5 5a2 2 0 012-2h10a2 2 0 012 2v16l-7-3.5L5 21V5z"
                />
              </svg>
            </button>

            <!-- Styled By -->
            <div class="flex items-center space-x-2">
              <span class="text-sm italic text-gray-900" style="font-family: 'Brush Script MT', cursive;">Styled by</span>
              <img
                :src="feedItem.user.avatar || '/default-avatar.png'"
                :alt="feedItem.user.username"
                class="w-6 h-6 rounded-full object-cover"
              />
              <router-link
                :to="`/profile/${feedItem.user.id}`"
                class="text-sm font-semibold text-gray-900 hover:text-blue-600"
              >
                {{ feedItem.user.username }}
              </router-link>
            </div>
          </div>
        </div>

        <!-- Tags Section -->
        <div v-if="tags.length > 0" class="mb-4 px-4 flex items-center space-x-2 overflow-x-auto pb-2">
          <button
            v-for="tag in tags"
            :key="tag"
            class="flex-shrink-0 inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
          >
            <svg class="w-4 h-4 mr-1.5 text-gray-500" fill="currentColor" viewBox="0 0 20 20">
              <path fill-rule="evenodd" d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z" clip-rule="evenodd" />
            </svg>
            {{ tag }}
          </button>
        </div>

        <!-- Actions and Info -->
        <div class="bg-white rounded-lg shadow-sm px-4 py-4">
          <!-- Like and Comment Buttons with Visibility Toggle -->
          <div class="flex items-center justify-between mb-3">
            <div class="flex items-center space-x-4">
              <button
                @click="handleLike"
                :disabled="liking"
                class="flex items-center transition-colors"
                :class="feedItem.is_liked_by_current_user ? 'text-red-500' : 'text-gray-600 hover:text-red-500'"
              >
                <svg
                  class="w-7 h-7"
                  :fill="feedItem.is_liked_by_current_user ? 'currentColor' : 'none'"
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
              </button>

              <button
                @click="openComments"
                class="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
              >
                <svg class="w-7 h-7" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z"
                  />
                </svg>
              </button>
            </div>

            <!-- Public/Private Toggle Button (only for image owner) -->
            <button
              v-if="isCurrentUserOwner"
              @click="handleToggleVisibility"
              class="flex items-center space-x-1.5 px-3 py-1.5 rounded-md text-sm font-medium transition-colors"
              :class="isPublic ? 'bg-blue-50 text-blue-700 hover:bg-blue-100' : 'bg-gray-100 text-gray-700 hover:bg-gray-200'"
            >
              <svg
                v-if="isPublic"
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"
                />
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M2.458 12C3.732 7.943 7.523 5 12 5c4.478 0 8.268 2.943 9.542 7-1.274 4.057-5.064 7-9.542 7-4.477 0-8.268-2.943-9.542-7z"
                />
              </svg>
              <svg
                v-else
                class="w-4 h-4"
                fill="none"
                stroke="currentColor"
                viewBox="0 0 24 24"
              >
                <path
                  stroke-linecap="round"
                  stroke-linejoin="round"
                  stroke-width="2"
                  d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21"
                />
              </svg>
              <span>{{ isPublic ? $t('communityDetail.public') : $t('communityDetail.private') }}</span>
            </button>
          </div>

          <!-- Like Count -->
          <div class="mb-3">
            <span class="font-semibold text-gray-900">{{ feedItem.like_count }} {{ $t('communityDetail.likes') }}</span>
          </div>

          <!-- Post Description -->
          <div class="mb-2">
            <span class="font-semibold text-gray-900 mr-2">{{ feedItem.user.username }}</span>
            <span class="text-gray-700">
              {{ showFullDescription ? feedItem.description : truncatedDescription }}
            </span>
            <button
              v-if="feedItem.description && feedItem.description.length > 100"
              @click="showFullDescription = !showFullDescription"
              class="ml-1 text-gray-500 hover:text-gray-700"
            >
              {{ showFullDescription ? $t('communityDetail.less') : $t('communityDetail.more') }}
            </button>
          </div>

          <!-- Timestamp -->
          <div class="text-xs text-gray-500">
            {{ formatTime(feedItem.created_at) }}
          </div>

          <!-- View Comments Link -->
          <button
            v-if="feedItem.comment_count > 0"
            @click="openComments"
            class="mt-2 text-sm text-gray-500 hover:text-gray-700"
          >
            {{ $t('communityDetail.viewAllComments', { count: feedItem.comment_count }) }}
          </button>
        </div>
      </div>

    <!-- Comment Modal -->
    <CommentModal
      :is-open="isCommentModalOpen"
      :image-id="feedItem?.id"
      @close="closeComments"
      @comment-added="handleCommentAdded"
      @comment-deleted="handleCommentDeleted"
    />

    <!-- Bottom Navigation -->
    <BottomNav />
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useCommunityStore } from '@/stores/community'
import { useAuthStore } from '@/stores/auth'
import BottomNav from '@/components/layout/BottomNav.vue'
import CommentModal from '@/components/modals/CommentModal.vue'
import brushIcon from '@/assets/icons/brush_icon.png'

const route = useRoute()
const router = useRouter()
const { t, locale } = useI18n()
const communityStore = useCommunityStore()
const authStore = useAuthStore()

// State
const feedItem = ref(null)
const loading = ref(false)
const error = ref(null)
const liking = ref(false)
const bookmarking = ref(false)
const isCommentModalOpen = ref(false)
const showFullDescription = ref(false)
const isPublic = ref(true) // Track visibility status

// Computed
const truncatedDescription = computed(() => {
  if (!feedItem.value?.description) return ''
  return feedItem.value.description.length > 100
    ? feedItem.value.description.substring(0, 100) + '...'
    : feedItem.value.description
})

const tags = computed(() => {
  // TODO: Replace with actual tags from API
  // For now, extract from style name or description
  const tagList = []
  if (feedItem.value?.style?.name) {
    tagList.push(feedItem.value.style.name)
  }
  // Mock additional tags
  if (feedItem.value?.id) {
    tagList.push('AI Art', 'Digital', 'Creative')
  }
  return tagList
})

// Check if the post author is also the style artist
const isAuthorArtist = computed(() => {
  if (!feedItem.value) return false
  // TODO: Replace with actual artist comparison when API is ready
  // For now, check if user has artist role or if user_id matches style artist_id
  return feedItem.value.user?.id === feedItem.value.style?.artist_id
})

// Check if current user owns this image
const isCurrentUserOwner = computed(() => {
  if (!authStore.isAuthenticated || !feedItem.value) return false
  return authStore.user?.id === feedItem.value.user?.id
})

// Methods
onMounted(async () => {
  await fetchFeedItem()
})

async function fetchFeedItem() {
  loading.value = true
  error.value = null
  try {
    const imageId = route.params.id

    // TODO: Replace with actual API call
    // const response = await getFeedItemById(imageId)
    // feedItem.value = response.data

    // Mock data for now - check if item exists in store
    const existingItem = communityStore.feed.find(item => item.id == imageId)

    if (existingItem) {
      feedItem.value = { ...existingItem }
    } else {
      // Mock data if not in store
      feedItem.value = {
        id: imageId,
        result_url: 'https://picsum.photos/800/800',
        description: 'Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua.',
        user: {
          id: 1,
          username: authStore.user?.username || 'Vincent',
          avatar: null,
        },
        style: {
          id: 1,
          name: 'Van Gogh Style',
          artist_id: 1, // Same as user.id to show brush icon
        },
        like_count: 100,
        comment_count: 5,
        is_liked_by_current_user: false,
        is_bookmarked: false,
        created_at: new Date(Date.now() - 1800000).toISOString(), // 30 minutes ago
      }
    }
  } catch (err) {
    console.error('Failed to fetch feed item:', err)
    error.value = t('communityDetail.loadFailed')
  } finally {
    loading.value = false
  }
}

async function handleLike() {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'Login', query: { returnUrl: route.fullPath } })
    return
  }

  if (liking.value) return

  liking.value = true
  try {
    // TODO: Replace with actual API call
    // await toggleLike(feedItem.value.id)

    // Update local state
    feedItem.value.is_liked_by_current_user = !feedItem.value.is_liked_by_current_user
    feedItem.value.like_count += feedItem.value.is_liked_by_current_user ? 1 : -1

    // Update in store if exists
    const storeItem = communityStore.feed.find(item => item.id === feedItem.value.id)
    if (storeItem) {
      storeItem.is_liked_by_current_user = feedItem.value.is_liked_by_current_user
      storeItem.like_count = feedItem.value.like_count
    }
  } catch (err) {
    console.error('Failed to toggle like:', err)
  } finally {
    liking.value = false
  }
}

async function handleBookmark() {
  if (!authStore.isAuthenticated) {
    router.push({ name: 'Login', query: { returnUrl: route.fullPath } })
    return
  }

  if (bookmarking.value) return

  bookmarking.value = true
  try {
    // TODO: Replace with actual API call
    // await toggleBookmark(feedItem.value.id)

    feedItem.value.is_bookmarked = !feedItem.value.is_bookmarked
  } catch (err) {
    console.error('Failed to toggle bookmark:', err)
  } finally {
    bookmarking.value = false
  }
}

async function handleToggleVisibility() {
  try {
    // TODO: Replace with actual API call
    // await updateImageVisibility(feedItem.value.id, !isPublic.value)

    // Toggle local state
    isPublic.value = !isPublic.value
    console.log('Image visibility toggled to:', isPublic.value ? 'Public' : 'Private')
  } catch (err) {
    console.error('Failed to toggle visibility:', err)
  }
}

function openComments() {
  // Just open the modal - authentication check will be done inside the modal if needed
  isCommentModalOpen.value = true
}

function closeComments() {
  isCommentModalOpen.value = false
}

function handleCommentAdded() {
  // Increment comment count
  feedItem.value.comment_count += 1

  // Update in store if exists
  const storeItem = communityStore.feed.find(item => item.id === feedItem.value.id)
  if (storeItem) {
    storeItem.comment_count = feedItem.value.comment_count
  }
}

function handleCommentDeleted() {
  // Decrement comment count
  feedItem.value.comment_count = Math.max(0, feedItem.value.comment_count - 1)

  // Update in store if exists
  const storeItem = communityStore.feed.find(item => item.id === feedItem.value.id)
  if (storeItem) {
    storeItem.comment_count = feedItem.value.comment_count
  }
}

function handleBack() {
  router.push('/community')
}

function formatTime(timestamp) {
  const now = new Date()
  const commentTime = new Date(timestamp)
  const diffInSeconds = Math.floor((now - commentTime) / 1000)

  if (diffInSeconds < 60) {
    return t('communityDetail.justNow')
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60)
    return minutes === 1
      ? t('communityDetail.minuteAgo', { count: minutes })
      : t('communityDetail.minutesAgo', { count: minutes })
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600)
    return hours === 1
      ? t('communityDetail.hourAgo', { count: hours })
      : t('communityDetail.hoursAgo', { count: hours })
  } else if (diffInSeconds < 604800) {
    const days = Math.floor(diffInSeconds / 86400)
    return days === 1
      ? t('communityDetail.dayAgo', { count: days })
      : t('communityDetail.daysAgo', { count: days })
  } else {
    const localeStr = locale.value === 'ko' ? 'ko-KR' : 'en-US'
    return commentTime.toLocaleDateString(localeStr, {
      month: 'short',
      day: 'numeric',
    })
  }
}
</script>
