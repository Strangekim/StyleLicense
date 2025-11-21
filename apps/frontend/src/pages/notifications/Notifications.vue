<template>
  <div class="min-h-screen bg-gray-50">
    <AppLayout>
      <!-- Header -->
      <div class="bg-white border-b border-gray-200 sticky top-0 z-10">
        <div class="max-w-3xl mx-auto px-4 py-4">
          <div class="flex items-center justify-between">
            <h1 class="text-2xl font-bold text-gray-900">
              {{ $t('notifications.title') }}
            </h1>
            <button
              v-if="hasUnread"
              @click="handleMarkAllAsRead"
              class="text-sm text-blue-600 hover:text-blue-700 font-medium"
              :disabled="loading"
            >
              {{ $t('notifications.markAllAsRead') }}
            </button>
          </div>
        </div>
      </div>

      <!-- Notifications List -->
      <div class="max-w-3xl mx-auto">
        <!-- Loading State -->
        <div v-if="loading && notifications.length === 0" class="p-8 text-center">
          <div class="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto"></div>
          <p class="mt-4 text-gray-600">{{ $t('common.loading') }}</p>
        </div>

        <!-- Empty State -->
        <div
          v-else-if="!loading && notifications.length === 0"
          class="p-12 text-center"
        >
          <svg
            class="mx-auto h-16 w-16 text-gray-400"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          <h3 class="mt-4 text-lg font-medium text-gray-900">
            {{ $t('notifications.empty.title') }}
          </h3>
          <p class="mt-2 text-gray-600">
            {{ $t('notifications.empty.description') }}
          </p>
        </div>

        <!-- Notification Items -->
        <div v-else class="bg-white divide-y divide-gray-200">
          <div
            v-for="notification in notifications"
            :key="notification.id"
            @click="handleNotificationClick(notification)"
            class="px-4 py-4 hover:bg-gray-50 cursor-pointer transition-colors"
            :class="{
              'bg-blue-50': !notification.is_read,
              'bg-white': notification.is_read,
            }"
          >
            <div class="flex items-start space-x-3">
              <!-- Icon -->
              <div
                class="flex-shrink-0 w-10 h-10 rounded-full flex items-center justify-center"
                :class="getNotificationIconClass(notification.notification_type)"
              >
                <svg class="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
                  <path :d="getNotificationIconPath(notification.notification_type)" />
                </svg>
              </div>

              <!-- Content -->
              <div class="flex-1 min-w-0">
                <p class="text-sm font-medium text-gray-900">
                  {{ notification.message }}
                </p>
                <p class="mt-1 text-xs text-gray-500">
                  {{ formatTime(notification.created_at) }}
                </p>
              </div>

              <!-- Unread Indicator -->
              <div v-if="!notification.is_read" class="flex-shrink-0">
                <div class="w-2 h-2 bg-blue-600 rounded-full"></div>
              </div>
            </div>
          </div>
        </div>

        <!-- Error State -->
        <div v-if="error" class="p-4 bg-red-50 text-red-800 rounded-md m-4">
          {{ error }}
        </div>
      </div>
    </AppLayout>
  </div>
</template>

<script setup>
import { ref, onMounted, computed } from 'vue'
import { useRouter } from 'vue-router'
import { useNotificationStore } from '@/stores/notification'
import AppLayout from '@/components/layout/AppLayout.vue'

const router = useRouter()
const notificationStore = useNotificationStore()

// State
const { notifications, loading, error, hasUnread } = notificationStore

// Methods
onMounted(async () => {
  await notificationStore.fetchNotifications()
})

async function handleMarkAllAsRead() {
  try {
    await notificationStore.markAllNotificationsAsRead()
  } catch (err) {
    console.error('Failed to mark all as read:', err)
  }
}

async function handleNotificationClick(notification) {
  try {
    // Mark as read
    if (!notification.is_read) {
      await notificationStore.markNotificationAsRead(notification.id)
    }

    // Navigate based on notification type
    const route = getNotificationRoute(notification)
    if (route) {
      router.push(route)
    }
  } catch (err) {
    console.error('Failed to handle notification click:', err)
  }
}

function getNotificationRoute(notification) {
  const { notification_type, related_id } = notification

  switch (notification_type) {
    case 'image_liked':
    case 'image_commented':
      return `/community/${related_id}`
    case 'model_training_completed':
    case 'model_training_failed':
      return `/styles/create`
    case 'image_generation_completed':
    case 'image_generation_failed':
      return `/generate/history`
    case 'new_follower':
      return `/profile`
    default:
      return null
  }
}

function getNotificationIconClass(type) {
  switch (type) {
    case 'image_liked':
      return 'bg-red-100 text-red-600'
    case 'image_commented':
      return 'bg-blue-100 text-blue-600'
    case 'model_training_completed':
      return 'bg-green-100 text-green-600'
    case 'model_training_failed':
    case 'image_generation_failed':
      return 'bg-red-100 text-red-600'
    case 'image_generation_completed':
      return 'bg-green-100 text-green-600'
    case 'new_follower':
      return 'bg-purple-100 text-purple-600'
    default:
      return 'bg-gray-100 text-gray-600'
  }
}

function getNotificationIconPath(type) {
  switch (type) {
    case 'image_liked':
      return 'M3.172 5.172a4 4 0 015.656 0L10 6.343l1.172-1.171a4 4 0 115.656 5.656L10 17.657l-6.828-6.829a4 4 0 010-5.656z' // Heart
    case 'image_commented':
      return 'M2 5a2 2 0 012-2h12a2 2 0 012 2v10a2 2 0 01-2 2H4a2 2 0 01-2-2V5zm3.293 1.293a1 1 0 011.414 0l3 3a1 1 0 010 1.414l-3 3a1 1 0 01-1.414-1.414L7.586 10 5.293 7.707a1 1 0 010-1.414z' // Comment
    case 'model_training_completed':
    case 'image_generation_completed':
      return 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z' // Check circle
    case 'model_training_failed':
    case 'image_generation_failed':
      return 'M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z' // X circle
    case 'new_follower':
      return 'M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z' // User
    default:
      return 'M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9' // Bell
  }
}

function formatTime(timestamp) {
  const now = new Date()
  const notificationTime = new Date(timestamp)
  const diffInSeconds = Math.floor((now - notificationTime) / 1000)

  if (diffInSeconds < 60) {
    return '방금 전'
  } else if (diffInSeconds < 3600) {
    const minutes = Math.floor(diffInSeconds / 60)
    return `${minutes}분 전`
  } else if (diffInSeconds < 86400) {
    const hours = Math.floor(diffInSeconds / 3600)
    return `${hours}시간 전`
  } else if (diffInSeconds < 604800) {
    const days = Math.floor(diffInSeconds / 86400)
    return `${days}일 전`
  } else {
    return notificationTime.toLocaleDateString('ko-KR', {
      month: 'short',
      day: 'numeric',
    })
  }
}
</script>
