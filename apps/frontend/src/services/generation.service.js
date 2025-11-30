/**
 * Image Generation Service
 *
 * Handles image generation operations including generating images and checking status.
 * Note: These endpoints will be implemented in M4 (AI Integration).
 */
import apiClient from './api'

/**
 * Generate image with style model
 *
 * @param {Object} data - Generation data
 * @param {number} data.style_id - Style model ID to use
 * @param {string} data.prompt - Text prompt or comma-separated tags
 * @param {string} data.aspect_ratio - Aspect ratio (1:1/2:2/1:2)
 * @param {number} data.seed - Random seed for reproducibility (optional)
 * @returns {Promise<Object>} Generation result with generation_id and status
 */
export async function generateImage(data) {
  const response = await apiClient.post('/api/generations/', data)
  return response.data
}

/**
 * Get image generation status
 *
 * @param {number} id - Generation ID
 * @returns {Promise<Object>} Generation status (queued/processing/completed/failed) and image_url if completed
 */
export async function getGenerationStatus(id) {
  const response = await apiClient.get(`/api/generations/${id}/`)
  return response.data
}

/**
 * List user's generation history
 *
 * @param {Object} params - Query parameters
 * @param {string} params.cursor - Pagination cursor (optional)
 * @param {number} params.limit - Number of results per page (default: 20)
 * @param {string} params.status - Filter by status (queued/processing/completed/failed)
 * @returns {Promise<Object>} Paginated list of generations
 */
export async function listGenerations(params = {}) {
  const response = await apiClient.get('/api/generations/', { params })
  return response.data
}

/**
 * Get generation detail
 *
 * @param {number} id - Generation ID
 * @returns {Promise<Object>} Generation detail with image, metadata, and artist info
 */
export async function getGenerationDetail(id) {
  const response = await apiClient.get(`/api/generations/${id}/`)
  return response.data
}

export default {
  generateImage,
  getGenerationStatus,
  listGenerations,
  getGenerationDetail,
}
