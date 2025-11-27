<template>
  <div class="min-h-screen bg-gray-50">
    <AppLayout>
      <div class="max-w-4xl mx-auto px-4 py-6">
        <!-- Loading State -->
        <div v-if="loading" class="flex justify-center items-center py-12">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
        </div>

        <!-- Profile Content -->
        <div v-else-if="profile">
          <!-- Profile Header -->
          <div class="bg-white rounded-lg shadow-sm p-6 mb-6">
            <div class="flex flex-col items-center text-center">
              <!-- Avatar -->
              <div class="relative mb-4">
                <div class="w-24 h-24 rounded-full overflow-hidden bg-gray-200 border-4 border-white shadow-md">
                  <img
                    v-if="profile.avatar"
                    :src="profile.avatar"
                    :alt="profile.username"
                    class="w-full h-full object-cover"
                  />
                  <div v-else class="w-full h-full flex items-center justify-center bg-blue-100 text-blue-600 text-3xl font-semibold">
                    {{ profile.username.charAt(0).toUpperCase() }}
                  </div>
                </div>
              </div>

              <!-- User Info -->
              <h1 class="text-xl font-bold text-gray-900 mb-1">
                {{ profile.display_name || profile.username }}
              </h1>
              <p class="text-sm text-gray-600 mb-1" v-if="profile.title">
                {{ profile.title }}
              </p>
              <p class="text-sm text-gray-700" v-if="profile.bio">
                {{ profile.bio }}
              </p>

              <!-- Stats (optional) -->
              <div class="flex items-center gap-6 mt-4 text-sm">
                <div class="text-center">
                  <div class="font-semibold text-gray-900">{{ profile.generation_count || 0 }}</div>
                  <div class="text-gray-500">{{ $t('profile.generations') }}</div>
                </div>
                <div class="text-center">
                  <div class="font-semibold text-gray-900">{{ profile.follower_count || 0 }}</div>
                  <div class="text-gray-500">{{ $t('profile.followers') }}</div>
                </div>
                <div class="text-center">
                  <div class="font-semibold text-gray-900">{{ profile.following_count || 0 }}</div>
                  <div class="text-gray-500">{{ $t('profile.following') }}</div>
                </div>
              </div>
            </div>

            <!-- Action Buttons -->
            <div class="grid grid-cols-2 md:grid-cols-4 gap-3 mt-6">
              <router-link
                to="/styles/create"
                class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-center"
              >
                {{ $t('profile.editStyle') }}
              </router-link>
              <router-link
                to="/tokens"
                class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-center"
              >
                {{ $t('profile.payment') }}
              </router-link>
              <router-link
                to="/profile/edit"
                class="px-4 py-2 text-sm font-medium text-gray-700 bg-white border border-gray-300 rounded-lg hover:bg-gray-50 transition-colors text-center"
              >
                {{ $t('profile.editProfile') }}
              </router-link>
              <button
                @click="handleLogout"
                class="px-4 py-2 text-sm font-medium text-red-600 bg-white border border-red-300 rounded-lg hover:bg-red-50 transition-colors"
              >
                {{ $t('nav.logout') }}
              </button>
            </div>
          </div>

          <!-- View Toggle -->
          <div class="flex items-center justify-center gap-4 mb-6">
            <button
              @click="viewMode = 'grid'"
              :class="[
                'p-2 rounded-lg transition-colors',
                viewMode === 'grid'
                  ? 'text-gray-900 bg-white shadow-sm'
                  : 'text-gray-400 hover:text-gray-600'
              ]"
              :aria-label="$t('common.grid')"
            >
              <svg class="w-6 h-6" fill="currentColor" viewBox="0 0 20 20">
                <path d="M5 3a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2V5a2 2 0 00-2-2H5zM5 11a2 2 0 00-2 2v2a2 2 0 002 2h2a2 2 0 002-2v-2a2 2 0 00-2-2H5zM11 5a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2V5zM11 13a2 2 0 012-2h2a2 2 0 012 2v2a2 2 0 01-2 2h-2a2 2 0 01-2-2v-2z" />
              </svg>
            </button>

            <button
              @click="viewMode = 'private'"
              :class="[
                'p-2 rounded-lg transition-colors',
                viewMode === 'private'
                  ? 'text-gray-900 bg-white shadow-sm'
                  : 'text-gray-400 hover:text-gray-600'
              ]"
              :aria-label="$t('common.private')"
            >
              <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
            </button>
          </div>

          <!-- Image Grid -->
          <div v-if="viewMode === 'grid'">
            <!-- Empty State -->
            <div v-if="!loadingImages && images.length === 0" class="text-center py-12">
              <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 16l4.586-4.586a2 2 0 012.828 0L16 16m-2-2l1.586-1.586a2 2 0 012.828 0L20 14m-6-6h.01M6 20h12a2 2 0 002-2V6a2 2 0 00-2-2H6a2 2 0 00-2 2v12a2 2 0 002 2z" />
              </svg>
              <h3 class="mt-4 text-lg font-medium text-gray-900">{{ $t('profile.noGenerationsYet') }}</h3>
              <p class="mt-2 text-gray-600">{{ $t('profile.startCreating') }}</p>
              <router-link
                to="/marketplace"
                class="mt-4 inline-block px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700"
              >
                {{ $t('profile.browseStyles') }}
              </router-link>
            </div>

            <!-- Image Grid -->
            <div v-else class="grid grid-cols-2 gap-4">
              <div
                v-for="image in images"
                :key="image.id"
                class="relative bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                @click="handleImageClick(image)"
              >
                <!-- Image -->
                <div class="aspect-square relative">
                  <!-- Loading State for Processing Images -->
                  <div
                    v-if="image.status === 'processing' || image.status === 'queued'"
                    class="absolute inset-0 flex items-center justify-center bg-gray-100"
                  >
                    <div class="text-center">
                      <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-2"></div>
                      <p class="text-sm text-gray-600">{{ image.status === 'queued' ? $t('profile.queued') : $t('profile.processing') }}</p>
                    </div>
                  </div>

                  <!-- Completed Image -->
                  <img
                    v-else-if="image.result_url"
                    :src="image.result_url"
                    :alt="image.description || 'Generated image'"
                    class="w-full h-full object-cover"
                  />

                  <!-- Failed State -->
                  <div
                    v-else-if="image.status === 'failed'"
                    class="absolute inset-0 flex items-center justify-center bg-red-50"
                  >
                    <div class="text-center text-red-600">
                      <svg class="w-12 h-12 mx-auto mb-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                      </svg>
                      <p class="text-sm">{{ $t('profile.failed') }}</p>
                    </div>
                  </div>

                  <!-- Visibility Badge (for private images) -->
                  <div
                    v-if="image.visibility === 'private'"
                    class="absolute top-2 right-2 bg-black bg-opacity-60 text-white px-2 py-1 rounded-full text-xs flex items-center"
                  >
                    <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                    {{ $t('profile.private') }}
                  </div>
                </div>

                <!-- Image Info (on hover) -->
                <div class="p-3 border-t border-gray-100">
                  <p class="text-xs text-gray-500 truncate">
                    {{ formatTime(image.created_at) }}
                  </p>
                  <div class="flex items-center gap-3 mt-1 text-xs text-gray-600">
                    <span class="flex items-center">
                      <svg class="w-4 h-4 mr-1" :fill="image.is_liked_by_current_user ? 'currentColor' : 'none'" :class="image.is_liked_by_current_user ? 'text-red-500' : ''" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z" />
                      </svg>
                      {{ image.like_count || 0 }}
                    </span>
                    <span class="flex items-center">
                      <svg class="w-4 h-4 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 12h.01M12 12h.01M16 12h.01M21 12c0 4.418-4.03 8-9 8a9.863 9.863 0 01-4.255-.949L3 20l1.395-3.72C3.512 15.042 3 13.574 3 12c0-4.418 4.03-8 9-8s9 3.582 9 8z" />
                      </svg>
                      {{ image.comment_count || 0 }}
                    </span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Loading More Images -->
            <div v-if="loadingImages" class="text-center py-8">
              <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600 mx-auto"></div>
            </div>
          </div>

          <!-- Private/Hidden View -->
          <div v-else-if="viewMode === 'private'">
            <div class="grid grid-cols-2 gap-4">
              <div
                v-for="image in privateImages"
                :key="image.id"
                class="relative bg-white rounded-lg overflow-hidden shadow-sm hover:shadow-md transition-shadow cursor-pointer"
                @click="handleImageClick(image)"
              >
                <div class="aspect-square relative">
                  <img
                    v-if="image.result_url"
                    :src="image.result_url"
                    :alt="image.description || 'Generated image'"
                    class="w-full h-full object-cover"
                  />
                  <div class="absolute top-2 right-2 bg-black bg-opacity-60 text-white px-2 py-1 rounded-full text-xs flex items-center">
                    <svg class="w-3 h-3 mr-1" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
                    </svg>
                    {{ $t('profile.private') }}
                  </div>
                </div>
                <div class="p-3 border-t border-gray-100">
                  <p class="text-xs text-gray-500 truncate">
                    {{ formatTime(image.created_at) }}
                  </p>
                </div>
              </div>
            </div>

            <!-- Empty State for Private -->
            <div v-if="privateImages.length === 0" class="text-center py-12">
              <svg class="mx-auto h-16 w-16 text-gray-400" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.875 18.825A10.05 10.05 0 0112 19c-4.478 0-8.268-2.943-9.543-7a9.97 9.97 0 011.563-3.029m5.858.908a3 3 0 114.243 4.243M9.878 9.878l4.242 4.242M9.88 9.88l-3.29-3.29m7.532 7.532l3.29 3.29M3 3l3.59 3.59m0 0A9.953 9.953 0 0112 5c4.478 0 8.268 2.943 9.543 7a10.025 10.025 0 01-4.132 5.411m0 0L21 21" />
              </svg>
              <h3 class="mt-4 text-lg font-medium text-gray-900">{{ $t('profile.noPrivateGenerations') }}</h3>
              <p class="mt-2 text-gray-600">{{ $t('profile.privateImagesWillAppear') }}</p>
            </div>
          </div>
        </div>
      </div>
    </AppLayout>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import { useAuthStore } from '@/stores/auth'
import AppLayout from '@/components/layout/AppLayout.vue'

const router = useRouter()
const { t, locale } = useI18n()
const authStore = useAuthStore()

// State
const profile = ref(null)
const images = ref([])
const loading = ref(false)
const loadingImages = ref(false)
const viewMode = ref('grid') // 'grid' or 'private'

// Computed
const privateImages = computed(() => {
  return images.value.filter(img => img.visibility === 'private')
})

// Methods
onMounted(async () => {
  await fetchProfile()
  await fetchUserImages()
})

async function fetchProfile() {
  loading.value = true
  try {
    // Use actual user data from auth store
    if (authStore.user) {
      profile.value = {
        id: authStore.user.id,
        username: authStore.user.username,
        display_name: authStore.user.username,  // Can add display_name field to backend if needed
        title: authStore.user.role === 'artist' ? 'Artist' : 'User',
        bio: authStore.user.bio || '',
        avatar: authStore.user.profile_image || null,
        generation_count: 0,  // TODO: Add to backend API
        follower_count: authStore.user.artist_profile?.follower_count || 0,
        following_count: 0,  // TODO: Add to backend API
      }
    }
  } catch (error) {
    console.error('Failed to fetch profile:', error)
  } finally {
    loading.value = false
  }
}

async function fetchUserImages() {
  loadingImages.value = true
  try {
    // TODO: Replace with actual API call
    // const response = await getUserGenerations()
    // images.value = response.data

    // Mock data
    images.value = [
      {
        id: 1,
        result_url: 'https://picsum.photos/400/400?random=1',
        description: 'Beautiful landscape',
        status: 'completed',
        visibility: 'public',
        like_count: 12,
        comment_count: 3,
        is_liked_by_current_user: false,
        created_at: new Date(Date.now() - 3600000).toISOString(),
      },
      {
        id: 2,
        result_url: null,
        description: 'Processing image',
        status: 'processing',
        visibility: 'public',
        like_count: 0,
        comment_count: 0,
        is_liked_by_current_user: false,
        created_at: new Date(Date.now() - 300000).toISOString(),
      },
      {
        id: 3,
        result_url: 'https://picsum.photos/400/400?random=3',
        description: 'Abstract art',
        status: 'completed',
        visibility: 'public',
        like_count: 45,
        comment_count: 8,
        is_liked_by_current_user: true,
        created_at: new Date(Date.now() - 7200000).toISOString(),
      },
      {
        id: 4,
        result_url: 'https://picsum.photos/400/400?random=4',
        description: 'Private work',
        status: 'completed',
        visibility: 'private',
        like_count: 0,
        comment_count: 0,
        is_liked_by_current_user: false,
        created_at: new Date(Date.now() - 86400000).toISOString(),
      },
      {
        id: 5,
        result_url: 'https://picsum.photos/400/400?random=5',
        description: 'Colorful design',
        status: 'completed',
        visibility: 'public',
        like_count: 23,
        comment_count: 5,
        is_liked_by_current_user: false,
        created_at: new Date(Date.now() - 172800000).toISOString(),
      },
      {
        id: 6,
        result_url: 'https://picsum.photos/400/400?random=6',
        description: 'Minimalist style',
        status: 'completed',
        visibility: 'public',
        like_count: 67,
        comment_count: 12,
        is_liked_by_current_user: true,
        created_at: new Date(Date.now() - 259200000).toISOString(),
      },
    ]
  } catch (error) {
    console.error('Failed to fetch user images:', error)
  } finally {
    loadingImages.value = false
  }
}

async function handleLogout() {
  try {
    await authStore.logout()
    // The logout function in auth store will redirect to /login
  } catch (error) {
    console.error('Logout failed:', error)
  }
}

function handleImageClick(image) {
  if (image.status === 'completed' && image.result_url) {
    router.push(`/community/${image.id}`)
  }
}

function formatTime(timestamp) {
  const now = new Date()
  const imageTime = new Date(timestamp)
  const diffInSeconds = Math.floor((now - imageTime) / 1000)

  if (diffInSeconds < 60) {
    return t('common.justNow')
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60)
    return t('common.minutesAgo', { n: minutes })
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600)
    return t('common.hoursAgo', { n: hours })
  } else if (diffInSeconds < 604800) {
    const days = Math.floor(diffInSeconds / 86400)
    return t('common.daysAgo', { n: days })
  } else {
    const localeStr = locale.value === 'ko' ? 'ko-KR' : 'en-US'
    return imageTime.toLocaleDateString(localeStr, {
      month: 'short',
      day: 'numeric',
    })
  }
}
</script>
