/**
 * Tag Service
 *
 * Handles tag operations including listing popular tags and autocomplete search.
 */
import apiClient from './api'

/**
 * List popular tags
 *
 * @param {Object} params - Query parameters
 * @param {string} params.search - Search query for autocomplete (optional)
 * @returns {Promise<Object>} List of tags with id, name, usage_count
 */
export async function listTags(params = {}) {
  const response = await apiClient.get('/api/tags/', { params })
  return response.data
}

/**
 * Get tag detail by ID
 *
 * @param {number} id - Tag ID
 * @returns {Promise<Object>} Tag detail with id, name, usage_count
 */
export async function getTagDetail(id) {
  const response = await apiClient.get(`/api/tags/${id}/`)
  return response.data
}

/**
 * Search tags by name (autocomplete)
 *
 * @param {string} query - Search query
 * @returns {Promise<Object>} List of matching tags
 */
export async function searchTags(query) {
  return listTags({ search: query })
}

export default {
  listTags,
  getTagDetail,
  searchTags,
}
