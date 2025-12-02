import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import apiClient from '@/services/api'
import { jwtDecode } from 'jwt-decode'

// Helper to set the Authorization header on the API client
const setAuthHeader = (token) => {
  if (token) {
    apiClient.defaults.headers.common['Authorization'] = `Bearer ${token}`
  } else {
    delete apiClient.defaults.headers.common['Authorization']
  }
}

export const useAuthStore = defineStore('auth', () => {
  // State
  const user = ref(null)
  const accessToken = ref(localStorage.getItem('accessToken') || null)
  const refreshToken = ref(localStorage.getItem('refreshToken') || null)
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const isAuthenticated = computed(() => !!accessToken.value && !!user.value)
  const isArtist = computed(() => user.value?.role === 'artist')
  const tokenBalance = computed(() => user.value?.token_balance || 0)

  // Actions

  /**
   * Initializes the auth state from localStorage and validates the token.
   */
  async function initAuth() {
    if (accessToken.value) {
      const decodedToken = jwtDecode(accessToken.value)
      const isExpired = decodedToken.exp * 1000 < Date.now()

      if (isExpired) {
        await attemptRefreshToken()
      } else {
        setAuthHeader(accessToken.value)
        await fetchCurrentUser()
      }
    }
  }

  /**
   * Fetches the current user's profile from the /api/auth/me endpoint.
   */
  async function fetchCurrentUser() {
    loading.value = true
    error.value = null
    try {
      const response = await apiClient.get('/api/auth/me')
      user.value = response.data
      loading.value = false
      return true
    } catch (err) {
      console.error('Failed to fetch current user:', err)
      error.value = err.response?.data?.error || 'Failed to fetch user'
      // If fetching user fails, clear auth state
      await logout()
      return false
    }
  }

  /**
   * Handles the token-based login after a successful OAuth callback.
   * @param {object} tokens - { access, refresh }
   */
  async function handleTokenLogin(tokens) {
    accessToken.value = tokens.access
    refreshToken.value = tokens.refresh

    localStorage.setItem('accessToken', tokens.access)
    localStorage.setItem('refreshToken', tokens.refresh)

    setAuthHeader(tokens.access)
    
    // After setting the token, fetch the user data
    await fetchCurrentUser()
  }
  
  /**
   * Attempts to refresh the access token using the refresh token.
   * @returns {boolean} - True if refresh was successful, false otherwise.
   */
  async function attemptRefreshToken() {
    if (!refreshToken.value) {
      return false
    }
    try {
      const response = await apiClient.post('/api/auth/token/refresh/', {
        refresh: refreshToken.value,
      })
      
      const newAccessToken = response.data.access
      accessToken.value = newAccessToken
      localStorage.setItem('accessToken', newAccessToken)
      setAuthHeader(newAccessToken)
      
      // After refreshing, fetch user data if it's missing
      if (!user.value) {
        await fetchCurrentUser()
      }
      return newAccessToken // Return the new token
    } catch (err) {
      console.error('Failed to refresh token:', err)
      // If refresh fails, log the user out completely
      await logout()
      return false
    }
  }

  /**
   * Logs the user out by clearing all auth-related state and storage.
   */
  async function logout() {
    loading.value = true
    try {
      // Optional: call a backend endpoint to blacklist the refresh token if implemented
      // await apiClient.post('/api/auth/logout/', { refresh: refreshToken.value });
    } catch (err) {
      console.error('Backend logout failed, proceeding with client-side logout.', err)
    } finally {
      user.value = null
      accessToken.value = null
      refreshToken.value = null

      localStorage.removeItem('accessToken')
      localStorage.removeItem('refreshToken')
      
      setAuthHeader(null)
      loading.value = false

      // Redirect to home page after logout
      window.location.href = '/login'
    }
  }

  return {
    // State
    user,
    loading,
    error,
    accessToken,
    // Getters
    isAuthenticated,
    isArtist,
    tokenBalance,
    // Actions
    initAuth,
    handleTokenLogin,
    fetchCurrentUser,
    attemptRefreshToken,
    logout,
  }
})
