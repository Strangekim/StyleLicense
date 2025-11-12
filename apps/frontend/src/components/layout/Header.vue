<template>
  <header class="sticky top-0 z-40 bg-white border-b border-neutral-200 shadow-sm">
    <div class="container mx-auto px-4">
      <div class="flex items-center justify-between h-16">
        <!-- Logo -->
        <router-link to="/" class="flex items-center gap-2 text-xl font-bold text-primary-600 hover:text-primary-700 transition-colors">
          <span>🎨</span>
          <span>Style License</span>
        </router-link>

        <!-- Desktop Navigation -->
        <nav class="hidden md:flex items-center gap-6">
          <router-link
            to="/"
            class="text-neutral-700 hover:text-primary-600 transition-colors font-medium"
            active-class="text-primary-600"
          >
            Marketplace
          </router-link>
          <router-link
            v-if="authStore.isAuthenticated"
            to="/generate"
            class="text-neutral-700 hover:text-primary-600 transition-colors font-medium"
            active-class="text-primary-600"
          >
            Generate
          </router-link>
          <router-link
            v-if="authStore.isArtist"
            to="/styles/create"
            class="text-neutral-700 hover:text-primary-600 transition-colors font-medium"
            active-class="text-primary-600"
          >
            Create Style
          </router-link>
        </nav>

        <!-- User Actions -->
        <div class="flex items-center gap-4">
          <!-- Token Balance (authenticated users only) -->
          <div
            v-if="authStore.isAuthenticated"
            class="hidden md:flex items-center gap-2 px-3 py-1.5 bg-primary-50 rounded-lg"
          >
            <span class="text-sm font-medium text-primary-700">💎</span>
            <span class="text-sm font-semibold text-primary-900">
              {{ authStore.user?.token_balance?.toLocaleString() || 0 }}
            </span>
          </div>

          <!-- Notification Dropdown (authenticated users only) -->
          <NotificationDropdown v-if="authStore.isAuthenticated" />

          <!-- User Dropdown (authenticated) -->
          <div v-if="authStore.isAuthenticated" class="relative" ref="dropdownRef">
            <button
              class="flex items-center gap-2 hover:bg-neutral-100 rounded-lg px-3 py-2 transition-colors"
              @click="toggleDropdown"
            >
              <div class="w-8 h-8 rounded-full bg-primary-100 flex items-center justify-center">
                <span class="text-sm font-semibold text-primary-700">
                  {{ authStore.user?.username?.charAt(0).toUpperCase() }}
                </span>
              </div>
              <svg class="w-4 h-4 text-neutral-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M19 9l-7 7-7-7" />
              </svg>
            </button>

            <!-- Dropdown Menu -->
            <Transition
              enter-active-class="transition duration-100 ease-out"
              enter-from-class="transform scale-95 opacity-0"
              enter-to-class="transform scale-100 opacity-100"
              leave-active-class="transition duration-75 ease-in"
              leave-from-class="transform scale-100 opacity-100"
              leave-to-class="transform scale-95 opacity-0"
            >
              <div
                v-if="isDropdownOpen"
                class="absolute right-0 mt-2 w-48 bg-white rounded-lg shadow-lg border border-neutral-200 py-1"
              >
                <router-link
                  to="/profile"
                  class="block px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100 transition-colors"
                  @click="closeDropdown"
                >
                  Profile
                </router-link>
                <router-link
                  to="/tokens"
                  class="block px-4 py-2 text-sm text-neutral-700 hover:bg-neutral-100 transition-colors"
                  @click="closeDropdown"
                >
                  Get Tokens
                </router-link>
                <hr class="my-1 border-neutral-200" />
                <button
                  class="w-full text-left px-4 py-2 text-sm text-red-600 hover:bg-red-50 transition-colors"
                  @click="handleLogout"
                >
                  Logout
                </button>
              </div>
            </Transition>
          </div>

          <!-- Login Button (not authenticated) -->
          <router-link
            v-else
            to="/login"
            class="px-4 py-2 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
          >
            Login
          </router-link>

          <!-- Mobile Menu Button -->
          <button
            class="md:hidden p-2 text-neutral-600 hover:text-neutral-900 transition-colors"
            @click="toggleMobileMenu"
          >
            <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
            </svg>
          </button>
        </div>
      </div>

      <!-- Mobile Menu -->
      <Transition
        enter-active-class="transition duration-200 ease-out"
        enter-from-class="transform -translate-y-2 opacity-0"
        enter-to-class="transform translate-y-0 opacity-100"
        leave-active-class="transition duration-150 ease-in"
        leave-from-class="transform translate-y-0 opacity-100"
        leave-to-class="transform -translate-y-2 opacity-0"
      >
        <div v-if="isMobileMenuOpen" class="md:hidden border-t border-neutral-200 py-4">
          <nav class="flex flex-col gap-2">
            <router-link
              to="/"
              class="px-4 py-2 text-neutral-700 hover:bg-neutral-100 rounded-lg transition-colors"
              @click="closeMobileMenu"
            >
              Marketplace
            </router-link>
            <router-link
              v-if="authStore.isAuthenticated"
              to="/generate"
              class="px-4 py-2 text-neutral-700 hover:bg-neutral-100 rounded-lg transition-colors"
              @click="closeMobileMenu"
            >
              Generate
            </router-link>
            <router-link
              v-if="authStore.isArtist"
              to="/styles/create"
              class="px-4 py-2 text-neutral-700 hover:bg-neutral-100 rounded-lg transition-colors"
              @click="closeMobileMenu"
            >
              Create Style
            </router-link>

            <!-- Mobile Token Balance -->
            <div
              v-if="authStore.isAuthenticated"
              class="mx-4 my-2 px-3 py-2 bg-primary-50 rounded-lg flex items-center justify-between"
            >
              <span class="text-sm font-medium text-primary-700">Token Balance</span>
              <span class="text-sm font-semibold text-primary-900">
                💎 {{ authStore.user?.token_balance?.toLocaleString() || 0 }}
              </span>
            </div>
          </nav>
        </div>
      </Transition>
    </div>
  </header>
</template>

<script setup>
import { ref, onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { useNotificationPolling } from '@/composables/useNotificationPolling'
import NotificationDropdown from '@/components/features/NotificationDropdown.vue'

const authStore = useAuthStore()
const router = useRouter()

// Start notification polling
const { startPolling, stopPolling } = useNotificationPolling()

const isDropdownOpen = ref(false)
const isMobileMenuOpen = ref(false)
const dropdownRef = ref(null)

const toggleDropdown = () => {
  isDropdownOpen.value = !isDropdownOpen.value
}

const closeDropdown = () => {
  isDropdownOpen.value = false
}

const toggleMobileMenu = () => {
  isMobileMenuOpen.value = !isMobileMenuOpen.value
}

const closeMobileMenu = () => {
  isMobileMenuOpen.value = false
}

const handleLogout = async () => {
  try {
    await authStore.logout()
    closeDropdown()
    router.push('/login')
  } catch (error) {
    console.error('Logout failed:', error)
  }
}

// Close dropdown when clicking outside
const handleClickOutside = (event) => {
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
