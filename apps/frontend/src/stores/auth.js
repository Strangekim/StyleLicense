import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { fetchMe, logout as logoutApi } from '@/services/auth'

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const isAuthenticated = computed(() => user.value !== null)
  const isArtist = computed(() => user.value?.role === 'artist')
  const tokenBalance = computed(() => user.value?.token_balance || 0)

  // Actions
  async function fetchCurrentUser() {
    loading.value = true
    error.value = null
    try {
      const response = await fetchMe()
      if (response.success) {
        user.value = response.data
        return true
      } else {
        user.value = null
        return false
      }
    } catch (err) {
      error.value = err.response?.data?.error?.message || 'Failed to fetch user'
      user.value = null
      return false
    } finally {
      loading.value = false
    }
  }

  async function logout() {
    loading.value = true
    error.value = null
    try {
      await logoutApi()
      user.value = null
      return true
    } catch (err) {
      error.value = err.response?.data?.error?.message || 'Logout failed'
      return false
    } finally {
      loading.value = false
    }
  }

  function clearUser() {
    user.value = null
    error.value = null
  }

  return {
    // State
    user,
    loading,
    error,
    // Getters
    isAuthenticated,
    isArtist,
    tokenBalance,
    // Actions
    fetchCurrentUser,
    logout,
    clearUser,
  }
})
