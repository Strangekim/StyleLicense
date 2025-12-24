/**
 * Style Model Service
 *
 * Handles style model operations including listing, detail view, creation, and deletion.
 */
import apiClient from './api'

/**
 * List style models with pagination and filters
 *
 * @param {Object} params - Query parameters
 * @param {string} params.cursor - Pagination cursor (optional)
 * @param {number} params.limit - Number of results per page (default: 20)
 * @param {string} params.tags - Comma-separated tag names for AND filtering (e.g. "watercolor,portrait")
 * @param {number} params.artist_id - Filter by artist ID
 * @param {string} params.training_status - Filter by training status (pending/training/completed/failed)
 * @param {string} params.sort - Sort by 'popular' or 'created_at' (default: '-created_at')
 * @returns {Promise<Object>} Paginated list of models with next/previous cursors
 */
export async function listModels(params = {}) {
  const response = await apiClient.get('/api/styles/', { params })
  return response.data
}

/**
 * Get style model detail by ID
 *
 * @param {number} id - Model ID
 * @returns {Promise<Object>} Model detail with artist info, artworks, and tags
 */
export async function getModelDetail(id) {
  const response = await apiClient.get(`/api/styles/${id}/`)
  return response.data
}

/**
 * Create new style model (artist only)
 *
 * @param {Object} data - Model creation data
 * @param {string} data.name - Model name
 * @param {string} data.description - Model description (optional)
 * @param {File[]} data.training_images - Array of image files (10-100 images)
 * @param {string[]} data.tags - Array of tag names (optional)
 * @param {File} data.signature - Signature image file (optional)
 * @returns {Promise<Object>} Created model with task_id
 */
export async function createModel(data) {
  const formData = new FormData()

  // Add basic fields
  formData.append('name', data.name)
  if (data.description) {
    formData.append('description', data.description)
  }
  if (data.generation_cost_tokens !== undefined) {
    formData.append('generation_cost_tokens', data.generation_cost_tokens)
  }

  // Add training images and captions
  if (data.training_images && data.training_images.length > 0) {
    data.training_images.forEach((image) => {
      // Extract file from object {file: File, caption: string}
      const file = image.file || image
      const caption = image.caption || ''

      formData.append('training_images', file)
      formData.append('captions', caption)
    })
  }

  // Add tags (each tag as separate field with same key)
  if (data.tags && data.tags.length > 0) {
    data.tags.forEach((tag) => {
      formData.append('tags', tag)
    })
  }

  // Add signature if provided
  if (data.signature) {
    formData.append('signature', data.signature)
  }

  const response = await apiClient.post('/api/styles/', formData, {
    headers: {
      'Content-Type': 'multipart/form-data',
    },
  })

  return response.data
}

/**
 * Get current artist's active style (MVP: 1 style per artist)
 *
 * @returns {Promise<Object>} Artist's style or null if none exists
 */
export async function getMyStyle() {
  try {
    const response = await apiClient.get('/api/styles/my-style/')
    return response.data
  } catch (error) {
    if (error.response?.status === 404) {
      return null // No style exists
    }
    throw error
  }
}

/**
 * Update existing style model (owner only, MVP: name and description only)
 *
 * @param {number} id - Model ID
 * @param {Object} data - Update data
 * @param {string} data.name - Model name (optional)
 * @param {string} data.description - Model description (optional)
 * @returns {Promise<Object>} Updated model
 */
export async function updateModel(id, data) {
  const response = await apiClient.patch(`/api/styles/${id}/`, data)
  return response.data
}

/**
 * Delete style model (owner only, soft delete)
 *
 * @param {number} id - Model ID
 * @returns {Promise<void>}
 */
export async function deleteModel(id) {
  const response = await apiClient.delete(`/api/styles/${id}/`)
  return response.data
}

/**
 * Get example generations for a style
 *
 * @param {number} id - Style ID
 * @returns {Promise<Object>} List of public generations created with this style
 */
export async function getStyleExampleGenerations(id) {
  const response = await apiClient.get(`/api/styles/${id}/example-generations/`)
  return response.data
}

/**
 * Get recommended tags for a style
 *
 * @param {number} id - Style ID
 * @returns {Promise<string[]>} Array of recommended tag names
 */
export async function getRecommendedTags(id) {
  try {
    const response = await apiClient.get(`/api/styles/${id}/recommended_tags/`)
    return response.data.data.recommended_tags || []
  } catch (error) {
    console.error('Failed to fetch recommended tags:', error)
    return [] // Graceful fallback
  }
}

export default {
  listModels,
  getModelDetail,
  getMyStyle,
  createModel,
  updateModel,
  deleteModel,
  getStyleExampleGenerations,
  getRecommendedTags,
}
