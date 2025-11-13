<script setup>
import { useAuthStore } from '@/stores/auth'
import { useRouter } from 'vue-router'
import { useI18n } from 'vue-i18n'
import logo from '@/assets/images/main_logo.webp'

const authStore = useAuthStore()
const router = useRouter()
const { t } = useI18n()

async function handleLogout() {
  const success = await authStore.logout()
  if (success) {
    router.push('/login')
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <header class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
        <div class="flex items-center space-x-3">
          <img :src="logo" alt="Style License" class="h-8 w-auto" />
          <h1 class="text-xl font-bold text-gray-900">{{ t('app.name') }}</h1>
        </div>

        <!-- User Info -->
        <div v-if="authStore.isAuthenticated" class="flex items-center space-x-4">
          <div class="text-sm text-gray-700">
            <span class="font-medium">{{ authStore.user?.username }}</span>
            <span class="ml-2 text-gray-500">
              ({{ authStore.tokenBalance }} {{ t('tokens.balance') }})
            </span>
          </div>
          <button
            @click="handleLogout"
            class="px-4 py-2 text-sm font-medium text-white bg-red-600 hover:bg-red-700 rounded-lg transition-colors duration-200"
          >
            {{ t('nav.logout') }}
          </button>
        </div>
        <div v-else>
          <router-link
            to="/login"
            class="px-4 py-2 text-sm font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors duration-200"
          >
            {{ t('nav.login') }}
          </router-link>
        </div>
      </div>
    </header>

    <!-- Main Content -->
    <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
      <div class="text-center">
        <h2 class="text-4xl font-bold text-gray-900 mb-4">
          {{ t('app.tagline') }}
        </h2>

        <div v-if="authStore.isAuthenticated" class="mt-8 space-y-4">
          <p class="text-lg text-gray-600">
            Welcome, {{ authStore.user?.username }}!
          </p>
          <div class="flex justify-center space-x-4">
            <div class="bg-white p-6 rounded-lg shadow">
              <p class="text-sm text-gray-500">Role</p>
              <p class="text-2xl font-bold text-gray-900">
                {{ authStore.user?.role }}
              </p>
            </div>
            <div class="bg-white p-6 rounded-lg shadow">
              <p class="text-sm text-gray-500">Token Balance</p>
              <p class="text-2xl font-bold text-gray-900">
                {{ authStore.tokenBalance }}
              </p>
            </div>
          </div>
        </div>

        <div v-else class="mt-8">
          <p class="text-lg text-gray-600 mb-4">
            Please login to continue
          </p>
          <router-link
            to="/login"
            class="inline-block px-6 py-3 text-base font-medium text-white bg-blue-600 hover:bg-blue-700 rounded-lg transition-colors duration-200"
          >
            {{ t('nav.login') }}
          </router-link>
        </div>
      </div>
    </main>
  </div>
</template>
