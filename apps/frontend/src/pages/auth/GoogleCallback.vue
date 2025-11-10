<script setup>
import { onMounted, ref } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useI18n } from 'vue-i18n'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const { t } = useI18n()

const loading = ref(true)
const error = ref(null)

onMounted(async () => {
  try {
    // Backend has already handled OAuth callback and set session cookie
    // Just fetch the current user to populate the store
    const success = await authStore.fetchCurrentUser()

    if (success) {
      // Get return URL from query params or default to home
      const returnUrl = route.query.returnUrl || '/'

      // Redirect to intended page
      await router.push(returnUrl)
    } else {
      // Failed to fetch user, redirect to login
      error.value = t('auth.loginError')
      setTimeout(() => {
        router.push('/login')
      }, 2000)
    }
  } catch (err) {
    console.error('OAuth callback error:', err)
    error.value = err.message || t('auth.loginError')

    // Redirect to login after showing error
    setTimeout(() => {
      router.push('/login')
    }, 2000)
  } finally {
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
    <div class="max-w-md w-full p-10 bg-white rounded-xl shadow-lg text-center">
      <!-- Loading State -->
      <div v-if="loading" class="space-y-4">
        <!-- Spinner -->
        <div class="flex justify-center">
          <svg
            class="animate-spin h-12 w-12 text-blue-600"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              class="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              stroke-width="4"
            />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
        <p class="text-gray-600">{{ t('auth.loggingIn') }}</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="space-y-4">
        <div class="text-red-500">
          <svg
            class="mx-auto h-12 w-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
            />
          </svg>
        </div>
        <p class="text-gray-900 font-medium">{{ error }}</p>
        <p class="text-sm text-gray-500">Redirecting to login...</p>
      </div>

      <!-- Success State (brief) -->
      <div v-else class="space-y-4">
        <div class="text-green-500">
          <svg
            class="mx-auto h-12 w-12"
            fill="none"
            stroke="currentColor"
            viewBox="0 0 24 24"
          >
            <path
              stroke-linecap="round"
              stroke-linejoin="round"
              stroke-width="2"
              d="M5 13l4 4L19 7"
            />
          </svg>
        </div>
        <p class="text-gray-900 font-medium">{{ t('auth.loginSuccess') }}</p>
      </div>
    </div>
  </div>
</template>
