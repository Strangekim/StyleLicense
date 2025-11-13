/**
 * Community service for feed, like, comment, and follow functionality
 */
import api from './api'

/**
 * Get community feed (public generations)
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @returns {Promise<Object>} - Feed list with pagination
 */
export async function getFeed(params = {}) {
  const response = await api.get('/community/', { params })
  return response.data
}

/**
 * Get generation detail
 * @param {number} generationId - Generation ID
 * @returns {Promise<Object>} - Generation detail
 */
export async function getGenerationDetail(generationId) {
  const response = await api.get(`/images/${generationId}/`)
  return response.data
}

/**
 * Toggle like on a generation
 * @param {number} generationId - Generation ID
 * @returns {Promise<Object>} - { is_liked, like_count }
 */
export async function toggleLike(generationId) {
  const response = await api.post(`/images/${generationId}/like/`)
  return response.data
}

/**
 * Get comments for a generation
 * @param {number} generationId - Generation ID
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} - Comments list with pagination
 */
export async function getComments(generationId, params = {}) {
  const response = await api.get(`/images/${generationId}/comments/`, { params })
  return response.data
}

/**
 * Add a comment to a generation
 * @param {number} generationId - Generation ID
 * @param {string} content - Comment content
 * @param {number|null} parentId - Parent comment ID (for replies)
 * @returns {Promise<Object>} - Created comment
 */
export async function addComment(generationId, content, parentId = null) {
  const response = await api.post(`/images/${generationId}/comments/`, {
    content,
    parent: parentId,
  })
  return response.data
}

/**
 * Delete a comment
 * @param {number} commentId - Comment ID
 * @returns {Promise<void>}
 */
export async function deleteComment(commentId) {
  await api.delete(`/comments/${commentId}/`)
}

/**
 * Toggle follow on a user
 * @param {number} userId - User ID to follow/unfollow
 * @returns {Promise<Object>} - { is_following, follower_count }
 */
export async function toggleFollow(userId) {
  const response = await api.post(`/users/${userId}/follow/`)
  return response.data
}

/**
 * Get list of users current user is following
 * @param {Object} params - Query parameters
 * @returns {Promise<Object>} - Following list with pagination
 */
export async function getFollowing(params = {}) {
  const response = await api.get('/users/following/', { params })
  return response.data
}
