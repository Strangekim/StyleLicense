/**
 * Authentication Service
 *
 * Handles user authentication operations including OAuth login, logout, and fetching current user.
 */
import apiClient from './api'

/**
 * Get Google OAuth login URL
 * User should be redirected to this URL to initiate OAuth flow
 *
 * @returns {string} OAuth login URL
 */
export function getGoogleLoginUrl() {
  // Use ?? instead of || to allow empty string (for Firebase Hosting rewrite)
  const baseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://localhost:8000'
  return `${baseUrl}/api/auth/google/login`
}

/**
 * Fetch current authenticated user
 *
 * @returns {Promise<Object>} User object with id, username, email, role, token_balance, etc.
 */
export async function getCurrentUser() {
  const response = await apiClient.get('/api/auth/me')
  return response.data
}

/**
 * Logout current user
 *
 * @returns {Promise<Object>} Success response
 */
export async function logout() {
  const response = await apiClient.post('/api/auth/logout')
  return response.data
}

export default {
  getGoogleLoginUrl,
  getCurrentUser,
  logout,
}
