<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { formatDistanceToNow } from '@/utils/date'

const notificationStore = useNotificationStore()
const isOpen = ref(false)
const dropdownRef = ref(null)

const notifications = computed(() => notificationStore.notifications.slice(0, 10))
const hasNotifications = computed(() => notifications.value.length > 0)

function toggleDropdown() {
  isOpen.value = !isOpen.value
}

function closeDropdown() {
  isOpen.value = false
}

async function handleNotificationClick(notification) {
  if (!notification.is_read) {
    try {
      await notificationStore.markNotificationAsRead(notification.id)
    } catch (error) {
      console.error('Failed to mark notification as read:', error)
    }
  }
  closeDropdown()
  // TODO: Navigate to related content based on notification type
}

async function handleMarkAllAsRead() {
  try {
    await notificationStore.markAllNotificationsAsRead()
  } catch (error) {
    console.error('Failed to mark all as read:', error)
  }
}

function getNotificationMessage(notification) {
  const actor = notification.actor_username || 'Someone'

  switch (notification.type) {
    case 'like':
      return `${actor} liked your generation`
    case 'comment':
      return `${actor} commented on your generation`
    case 'follow':
      return `${actor} started following you`
    case 'generation_complete':
      return 'Your generation is ready!'
    case 'generation_failed':
      return 'Generation failed'
    case 'style_training_complete':
      return 'Your style model is ready!'
    case 'style_training_failed':
      return 'Style training failed'
    default:
      return 'New notification'
  }
}

// Click outside to close
function handleClickOutside(event) {
  if (dropdownRef.value && !dropdownRef.value.contains(event.target)) {
    closeDropdown()
  }
}

onMounted(() => {
  document.addEventListener('click', handleClickOutside)
})

onUnmounted(() => {
  document.removeEventListener('click', handleClickOutside)
})
</script>

<template>
  <div ref="dropdownRef" class="relative">
    <!-- Notification Bell Button -->
    <button
      @click="toggleDropdown"
      class="relative p-2 text-gray-600 hover:text-gray-900 focus:outline-none focus:ring-2 focus:ring-primary-500 rounded-lg transition-colors"
      :aria-label="`Notifications${notificationStore.hasUnread ? ` (${notificationStore.unreadCount} unread)` : ''}`"
    >
      <!-- Bell Icon -->
      <svg
        xmlns="http://www.w3.org/2000/svg"
        class="h-6 w-6"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
        />
      </svg>

      <!-- Badge -->
      <span
        v-if="notificationStore.hasUnread"
        class="absolute top-1 right-1 inline-flex items-center justify-center px-1.5 py-0.5 text-xs font-bold leading-none text-white bg-red-500 rounded-full min-w-[18px]"
      >
        {{ notificationStore.unreadCount > 99 ? '99+' : notificationStore.unreadCount }}
      </span>
    </button>

    <!-- Dropdown -->
    <transition
      enter-active-class="transition ease-out duration-100"
      enter-from-class="transform opacity-0 scale-95"
      enter-to-class="transform opacity-100 scale-100"
      leave-active-class="transition ease-in duration-75"
      leave-from-class="transform opacity-100 scale-100"
      leave-to-class="transform opacity-0 scale-95"
    >
      <div
        v-if="isOpen"
        class="absolute right-0 mt-2 w-80 bg-white rounded-lg shadow-lg ring-1 ring-black ring-opacity-5 z-50"
      >
        <!-- Header -->
        <div class="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <h3 class="text-sm font-semibold text-gray-900">Notifications</h3>
          <button
            v-if="notificationStore.hasUnread"
            @click="handleMarkAllAsRead"
            class="text-xs text-primary-600 hover:text-primary-700 font-medium"
          >
            Mark all as read
          </button>
        </div>

        <!-- Notification List -->
        <div class="max-h-96 overflow-y-auto">
          <div v-if="notificationStore.loading && !hasNotifications" class="px-4 py-8 text-center">
            <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600 mx-auto"></div>
            <p class="mt-2 text-sm text-gray-500">Loading...</p>
          </div>

          <div v-else-if="!hasNotifications" class="px-4 py-8 text-center">
            <svg
              xmlns="http://www.w3.org/2000/svg"
              class="h-12 w-12 mx-auto text-gray-400"
              fill="none"
              viewBox="0 0 24 24"
              stroke="currentColor"
            >
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M20 13V6a2 2 0 00-2-2H6a2 2 0 00-2 2v7m16 0v5a2 2 0 01-2 2H6a2 2 0 01-2-2v-5m16 0h-2.586a1 1 0 00-.707.293l-2.414 2.414a1 1 0 01-.707.293h-3.172a1 1 0 01-.707-.293l-2.414-2.414A1 1 0 006.586 13H4"
              />
            </svg>
            <p class="mt-2 text-sm text-gray-500">No notifications yet</p>
          </div>

          <div v-else>
            <button
              v-for="notification in notifications"
              :key="notification.id"
              @click="handleNotificationClick(notification)"
              class="w-full px-4 py-3 hover:bg-gray-50 transition-colors text-left border-b border-gray-100 last:border-b-0"
              :class="{ 'bg-blue-50': !notification.is_read }"
            >
              <div class="flex items-start space-x-3">
                <!-- Avatar or Icon -->
                <div class="flex-shrink-0">
                  <img
                    v-if="notification.actor_profile_image"
                    :src="notification.actor_profile_image"
                    :alt="notification.actor_username"
                    class="h-10 w-10 rounded-full object-cover"
                  />
                  <div
                    v-else
                    class="h-10 w-10 rounded-full bg-gradient-to-br from-primary-400 to-primary-600 flex items-center justify-center"
                  >
                    <span class="text-white text-sm font-medium">
                      {{ (notification.actor_username || 'S')[0].toUpperCase() }}
                    </span>
                  </div>
                </div>

                <!-- Content -->
                <div class="flex-1 min-w-0">
                  <p class="text-sm text-gray-900">
                    {{ getNotificationMessage(notification) }}
                  </p>
                  <p class="text-xs text-gray-500 mt-1">
                    {{ formatDistanceToNow(notification.created_at) }}
                  </p>
                </div>

                <!-- Unread Indicator -->
                <div v-if="!notification.is_read" class="flex-shrink-0">
                  <div class="h-2 w-2 bg-blue-500 rounded-full"></div>
                </div>
              </div>
            </button>
          </div>
        </div>

        <!-- Footer -->
        <div v-if="hasNotifications" class="px-4 py-3 border-t border-gray-200 text-center">
          <router-link
            to="/notifications"
            @click="closeDropdown"
            class="text-sm text-primary-600 hover:text-primary-700 font-medium"
          >
            View all notifications
          </router-link>
        </div>
      </div>
    </transition>
  </div>
</template>
