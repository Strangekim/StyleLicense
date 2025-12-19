<template>
  <header class="sticky top-0 z-40 bg-white border-b border-gray-200">
    <div class="max-w-screen-sm mx-auto px-4 h-14 flex items-center justify-between">
      <!-- Logo -->
      <router-link to="/" class="flex items-center">
        <img
          src="@/assets/images/main_typo.png"
          alt="Style License"
          class="h-10"
        />
      </router-link>

      <!-- Right Side Icons -->
      <div class="flex items-center gap-2">
        <!-- Language Switcher -->
        <button
          @click="toggleLanguage"
          class="p-2 text-gray-700 hover:text-gray-900 transition-colors flex items-center gap-1"
          :title="`Switch to ${locale === 'en' ? '한국어' : 'English'}`"
        >
          <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M3 5h12M9 3v2m1.048 9.5A18.022 18.022 0 016.412 9m6.088 9h7M11 21l5-10 5 10M12.751 5C11.783 10.77 8.07 15.61 3 18.129"
            />
          </svg>
          <span class="text-xs font-medium">{{ locale === 'en' ? 'EN' : 'KO' }}</span>
        </button>

        <!-- Notification Icon -->
        <router-link
          to="/notifications"
          class="p-2 text-gray-700 hover:text-gray-900 transition-colors relative"
        >
          <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M15 17h5l-1.405-1.405A2.032 2.032 0 0118 14.158V11a6.002 6.002 0 00-4-5.659V5a2 2 0 10-4 0v.341C7.67 6.165 6 8.388 6 11v3.159c0 .538-.214 1.055-.595 1.436L4 17h5m6 0v1a3 3 0 11-6 0v-1m6 0H9"
            />
          </svg>
          <!-- Unread badge (optional) -->
          <span
            v-if="hasUnread"
            class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full"
          ></span>
        </router-link>
      </div>
    </div>
  </header>
</template>

<script setup>
import { onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'

// i18n setup
const { locale } = useI18n()

// Notification store
const notificationStore = useNotificationStore()
const authStore = useAuthStore()
const { hasUnread } = notificationStore

// Toggle language between en and ko
const toggleLanguage = () => {
  locale.value = locale.value === 'en' ? 'ko' : 'en'
  // Optionally save to localStorage
  localStorage.setItem('preferredLanguage', locale.value)
}

// Load preferred language on mount
const loadPreferredLanguage = () => {
  const saved = localStorage.getItem('preferredLanguage')
  if (saved && (saved === 'en' || saved === 'ko')) {
    locale.value = saved
  }
}

// Fetch unread notification count on mount
onMounted(async () => {
  loadPreferredLanguage()

  // Only fetch if user is authenticated
  if (authStore.isAuthenticated) {
    try {
      await notificationStore.fetchNotifications({ page: 1, page_size: 1 })
    } catch (err) {
      console.error('Failed to fetch notification count:', err)
    }
  }
})
</script>
