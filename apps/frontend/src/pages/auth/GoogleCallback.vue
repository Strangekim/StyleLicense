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
  const { access_token, refresh_token } = route.query

  if (access_token && refresh_token) {
    try {
      // Handle the token login
      await authStore.handleTokenLogin({ access: access_token, refresh: refresh_token })
      
      // Redirect to home or intended page
      const returnUrl = localStorage.getItem('post_login_return_url') || '/'
      localStorage.removeItem('post_login_return_url')
      
      await router.push(returnUrl)

    } catch (err) {
      console.error('Token login error:', err)
      error.value = t('auth.loginError')
      setTimeout(() => router.push('/login'), 3000)
    } finally {
      loading.value = false
    }
  } else {
    // No tokens found in URL
    console.error('No tokens provided in callback URL')
    error.value = t('auth.missingTokens')
    setTimeout(() => router.push('/login'), 3000)
    loading.value = false
  }
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-indigo-100">
    <div class="max-w-md w-full p-10 bg-white rounded-xl shadow-lg text-center">
      <!-- Loading State -->
      <div v-if="loading" class="space-y-4">
        <div class="flex justify-center">
          <svg
            class="animate-spin h-12 w-12 text-blue-600"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle class="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" stroke-width="4" />
            <path
              class="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
        </div>
        <p class="text-gray-600">{{ t('auth.processingLogin') }}</p>
      </div>

      <!-- Error State -->
      <div v-else-if="error" class="space-y-4">
        <div class="text-red-500">
          <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
          </svg>
        </div>
        <p class="text-gray-900 font-medium">{{ error }}</p>
        <p class="text-sm text-gray-500">Redirecting to login...</p>
      </div>

      <!-- Success State (brief) -->
      <div v-else class="space-y-4">
        <div class="text-green-500">
          <svg class="mx-auto h-12 w-12" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7" />
          </svg>
        </div>
        <p class="text-gray-900 font-medium">{{ t('auth.loginSuccess') }}</p>
      </div>
    </div>
  </div>
</template>
