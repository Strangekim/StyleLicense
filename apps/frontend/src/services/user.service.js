/**
 * User Service
 * Handles user profile and related operations
 */

import api from './api'

/**
 * Get user profile by ID
 * @param {number} userId - User ID
 * @returns {Promise<Object>} - User profile data
 */
export async function getUserProfile(userId) {
  const response = await api.get(`/api/users/${userId}`)
  return response.data
}

/**
 * Update current user's profile
 * @param {Object} data - Profile data to update
 * @param {string} data.username - Username
 * @param {string} data.bio - Bio text
 * @param {File} data.profile_image - Profile image file (optional)
 * @returns {Promise<Object>} - Updated profile data
 */
export async function updateUserProfile(data) {
  // Handle file upload separately if profile_image is a File
  if (data.profile_image instanceof File) {
    const formData = new FormData()
    formData.append('profile_image', data.profile_image)
    if (data.username) formData.append('username', data.username)
    if (data.bio) formData.append('bio', data.bio)

    const response = await api.patch('/api/users/me/', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    })
    return response.data
  } else {
    // Regular JSON update
    const response = await api.patch('/api/users/me/', data)
    return response.data
  }
}

/**
 * Upgrade to artist account
 * @returns {Promise<Object>} - Upgraded artist data
 */
export async function upgradeToArtist() {
  const response = await api.post('/api/users/upgrade-to-artist/')
  return response.data
}

/**
 * Get user's generations
 * @param {number} userId - User ID
 * @param {Object} params - Query parameters
 * @param {string} params.cursor - Pagination cursor
 * @param {number} params.limit - Limit per page
 * @param {string} params.status - Filter by status (completed, processing, etc.)
 * @param {string} params.visibility - Filter by visibility (public, private)
 * @returns {Promise<Object>} - Generations list with pagination
 */
export async function getUserGenerations(userId, params = {}) {
  // If requesting current user's generations
  if (userId === 'me' || !userId) {
    const response = await api.get('/api/generations/me/', { params })
    return response.data
  }

  // For other users, use the feed endpoint with user filter
  // TODO: Backend needs to add user_id filter to feed endpoint
  const response = await api.get('/api/generations/feed/', {
    params: {
      ...params,
      user_id: userId,
    },
  })
  return response.data
}
