import axios from 'axios'

// Get API base URL from environment variable
const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000'

// Create Axios instance
const apiClient = axios.create({
  baseURL: API_BASE_URL,
  timeout: 30000,
  withCredentials: true, // Include cookies for session-based auth
  headers: {
    'Content-Type': 'application/json',
  },
})

// Request interceptor
apiClient.interceptors.request.use(
  (config) => {
    // Get CSRF token from cookie if available
    const csrfToken = getCookie('csrftoken')
    if (csrfToken && ['post', 'put', 'patch', 'delete'].includes(config.method)) {
      config.headers['X-CSRFToken'] = csrfToken
    }

    // Log requests in development mode
    if (import.meta.env.DEV) {
      console.log(`[API Request] ${config.method.toUpperCase()} ${config.url}`, config.data)
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor
apiClient.interceptors.response.use(
  (response) => {
    // Log responses in development mode
    if (import.meta.env.DEV) {
      console.log(`[API Response] ${response.config.method.toUpperCase()} ${response.config.url}`, response.data)
    }

    // Extract data from response.data if present
    return response
  },
  (error) => {
    const { response } = error

    // Log errors in development mode
    if (import.meta.env.DEV) {
      console.error('[API Error]', error.response?.data || error.message)
    }

    // Handle different error statuses
    if (response) {
      switch (response.status) {
        case 401:
          // Unauthorized - redirect to login
          // Only redirect if not already on login page
          if (!window.location.pathname.includes('/login')) {
            window.location.href = '/login'
          }
          break
        case 403:
          // Forbidden - show permission denied message
          console.error('Permission denied:', response.data?.error?.message)
          break
        case 500:
          // Internal server error
          console.error('Server error:', response.data?.error?.message)
          break
      }
    }

    return Promise.reject(error)
  }
)

// Helper function to get cookie value by name
function getCookie(name) {
  const value = `; ${document.cookie}`
  const parts = value.split(`; ${name}=`)
  if (parts.length === 2) return parts.pop().split(';').shift()
  return null
}

export default apiClient
