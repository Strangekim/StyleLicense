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

  // Add training images
  if (data.training_images && data.training_images.length > 0) {
    data.training_images.forEach((image) => {
      // Extract file from object {file: File, caption: string}
      const file = image.file || image
      formData.append('training_images', file)
    })
  }

  // Add tags as JSON string
  if (data.tags && data.tags.length > 0) {
    formData.append('tags', JSON.stringify(data.tags))
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
 * Delete style model (owner only, soft delete)
 *
 * @param {number} id - Model ID
 * @returns {Promise<void>}
 */
export async function deleteModel(id) {
  const response = await apiClient.delete(`/api/styles/${id}/`)
  return response.data
}

export default {
  listModels,
  getModelDetail,
  createModel,
  deleteModel,
}
