<template>
  <nav class="fixed bottom-0 left-0 right-0 bg-white border-t border-gray-200 z-40">
    <div class="max-w-screen-sm mx-auto px-4 h-16 flex items-center justify-around">
      <!-- Home -->
      <router-link
        to="/"
        class="flex flex-col items-center justify-center flex-1 py-2 text-gray-600 hover:text-gray-900 transition-colors"
        active-class="text-gray-900"
      >
        <svg class="w-7 h-7 mb-0.5" fill="currentColor" viewBox="0 0 20 20">
          <path d="M10.707 2.293a1 1 0 00-1.414 0l-7 7a1 1 0 001.414 1.414L4 10.414V17a1 1 0 001 1h2a1 1 0 001-1v-2a1 1 0 011-1h2a1 1 0 011 1v2a1 1 0 001 1h2a1 1 0 001-1v-6.586l.293.293a1 1 0 001.414-1.414l-7-7z" />
        </svg>
        <div
          class="h-1 w-12 rounded-full transition-colors"
          :class="isActive('/') ? 'bg-black' : 'bg-transparent'"
        ></div>
      </router-link>

      <!-- Generate/Create -->
      <router-link
        to="/marketplace"
        class="flex flex-col items-center justify-center flex-1 py-2"
      >
        <img
          :src="isActive('/marketplace') || isActive('/generate') ? styleIconSelected : styleIcon"
          alt="Marketplace"
          class="w-7 h-7 mb-0.5"
        />
        <div
          class="h-1 w-12 rounded-full transition-colors"
          :class="isActive('/marketplace') || isActive('/generate') ? 'bg-black' : 'bg-transparent'"
        ></div>
      </router-link>

      <!-- Profile -->
      <router-link
        to="/profile"
        class="flex flex-col items-center justify-center flex-1 py-2 text-gray-600 hover:text-gray-900 transition-colors"
        active-class="text-gray-900"
      >
        <div class="w-7 h-7 rounded-full bg-gray-300 mb-0.5 overflow-hidden">
          <img
            v-if="user?.avatar"
            :src="user.avatar"
            alt="Profile"
            class="w-full h-full object-cover"
          />
          <div v-else class="w-full h-full flex items-center justify-center text-gray-600 text-sm font-semibold">
            {{ user?.username?.charAt(0).toUpperCase() || 'U' }}
          </div>
        </div>
        <div
          class="h-1 w-12 rounded-full transition-colors"
          :class="isActive('/profile') ? 'bg-black' : 'bg-transparent'"
        ></div>
      </router-link>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import styleIcon from '@/assets/icons/style_icon.png'
import styleIconSelected from '@/assets/icons/style_icon_selected.png'

const route = useRoute()
const authStore = useAuthStore()

const user = computed(() => authStore.user)

function isActive(path) {
  if (path === '/') {
    return route.path === '/' || route.path === '/community'
  }
  return route.path.startsWith(path)
}
</script>
