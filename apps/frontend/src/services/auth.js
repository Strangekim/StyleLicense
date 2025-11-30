import apiClient from './api'

/**
 * Fetch current authenticated user information
 * @returns {Promise} User data
 */
export async function fetchMe() {
  const response = await apiClient.get('/api/auth/me')
  return response.data
}

/**
 * Logout current user
 * @returns {Promise} Success message
 */
export async function logout() {
  const response = await apiClient.post('/api/auth/logout')
  return response.data
}

/**
 * Get Google OAuth login URL
 * Note: This is not an API call, just returns the backend OAuth URL
 * @returns {string} Google OAuth URL
 */
export function getGoogleOAuthUrl() {
  // Use ?? instead of || to allow empty string (for Firebase Hosting rewrite)
  const baseURL = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
  return `${baseURL}/api/auth/google/login`
}
