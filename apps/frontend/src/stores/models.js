/**
 * Models Store (Style Models)
 *
 * Manages style model state including listing, detail view, creation, and deletion.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import modelService from '@/services/model.service'

export const useModelsStore = defineStore('models', () => {
  // State
  const models = ref([])
  const currentModel = ref(null)
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({
    next: null,
    previous: null,
  })

  // Getters
  const hasMore = computed(() => pagination.value.next !== null)
  const modelCount = computed(() => models.value.length)

  /**
   * Fetch models with filters
   * @param {Object} params - Query parameters (tags, artist_id, training_status, sort, cursor, limit)
   * @param {boolean} append - Whether to append to existing list (for infinite scroll)
   */
  const fetchModels = async (params = {}, append = false) => {
    try {
      loading.value = true
      error.value = null

      const response = await modelService.listModels(params)

      if (response.success) {
        const data = response.data

        if (append) {
          models.value.push(...data.results)
        } else {
          models.value = data.results
        }

        pagination.value = {
          next: data.next,
          previous: data.previous,
        }
      }
    } catch (err) {
      console.warn('Failed to fetch models from API, using mock data:', err)

      // Mock data for development
      const mockModels = [
        {
          id: 1,
          name: 'Van Gogh Style',
          description: 'Expressive brushstrokes inspired by Van Gogh',
          thumbnail_url: 'https://picsum.photos/300/300?random=1',
          sample_images: [
            'https://picsum.photos/400/400?random=1',
            'https://picsum.photos/400/400?random=2',
            'https://picsum.photos/400/400?random=3',
          ],
          artist: {
            id: 1,
            username: 'Vincent',
            avatar: null,
          },
          training_status: 'completed',
          usage_count: 1250,
          price_per_generation: 5,
          created_at: new Date(Date.now() - 7 * 86400000).toISOString(), // 7 days ago
        },
        {
          id: 2,
          name: 'Abstract Modern',
          description: 'Bold colors and geometric shapes',
          thumbnail_url: 'https://picsum.photos/300/300?random=4',
          sample_images: [
            'https://picsum.photos/400/400?random=4',
            'https://picsum.photos/400/400?random=5',
          ],
          artist: {
            id: 2,
            username: 'ModernArtist',
            avatar: null,
          },
          training_status: 'completed',
          usage_count: 850,
          price_per_generation: 3,
          created_at: new Date(Date.now() - 14 * 86400000).toISOString(), // 14 days ago
        },
        {
          id: 3,
          name: 'Impressionist',
          description: 'Soft brushstrokes and light effects',
          thumbnail_url: 'https://picsum.photos/300/300?random=6',
          sample_images: [
            'https://picsum.photos/400/400?random=6',
            'https://picsum.photos/400/400?random=7',
            'https://picsum.photos/400/400?random=8',
          ],
          artist: {
            id: 1,
            username: 'Vincent',
            avatar: null,
          },
          training_status: 'completed',
          usage_count: 2100,
          price_per_generation: 4,
          created_at: new Date(Date.now() - 30 * 86400000).toISOString(), // 30 days ago
        },
      ]

      if (append) {
        models.value.push(...mockModels)
      } else {
        models.value = mockModels
      }

      pagination.value = {
        next: null,
        previous: null,
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch model detail by ID
   * @param {number} id - Model ID
   */
  const fetchModelDetail = async (id) => {
    try {
      loading.value = true
      error.value = null

      const response = await modelService.getModelDetail(id)

      if (response.success) {
        currentModel.value = response.data
      }
    } catch (err) {
      console.warn('Failed to fetch model detail from API, using mock data:', err)

      // Check if we have this model in the list
      const existingModel = models.value.find(m => m.id == id)

      if (existingModel) {
        currentModel.value = existingModel
      } else {
        // Fallback mock data
        currentModel.value = {
          id: parseInt(id),
          name: 'Van Gogh Style',
          description: 'Expressive brushstrokes inspired by Van Gogh. Perfect for creating artistic interpretations of your photos.',
          thumbnail_url: 'https://picsum.photos/300/300?random=1',
          sample_images: [
            'https://picsum.photos/400/400?random=1',
            'https://picsum.photos/400/400?random=2',
            'https://picsum.photos/400/400?random=3',
          ],
          artist: {
            id: 1,
            username: 'Vincent',
            avatar: null,
          },
          training_status: 'completed',
          usage_count: 1250,
          price_per_generation: 5,
          created_at: new Date(Date.now() - 7 * 86400000).toISOString(),
        }
      }
    } finally {
      loading.value = false
    }
  }

  /**
   * Create new style model (artist only)
   * @param {Object} data - Model creation data
   * @returns {Object} Created model data
   */
  const createModel = async (data) => {
    try {
      loading.value = true
      error.value = null

      const response = await modelService.createModel(data)

      if (response.success) {
        // Add to beginning of list if we're on the first page
        if (!pagination.value.previous) {
          models.value.unshift(response.data)
        }
        return response.data
      }
    } catch (err) {
      error.value = err.response?.data?.error?.message || 'Failed to create model'
      console.error('Error creating model:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Delete style model (owner only)
   * @param {number} id - Model ID
   */
  const deleteModel = async (id) => {
    try {
      loading.value = true
      error.value = null

      await modelService.deleteModel(id)

      // Remove from list
      models.value = models.value.filter((model) => model.id !== id)

      // Clear current model if it's the one being deleted
      if (currentModel.value?.id === id) {
        currentModel.value = null
      }
    } catch (err) {
      error.value = err.response?.data?.error?.message || 'Failed to delete model'
      console.error('Error deleting model:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Load more models (for infinite scroll)
   */
  const loadMore = async () => {
    if (!hasMore.value || loading.value) return

    // Extract cursor from next URL
    const nextUrl = new URL(pagination.value.next)
    const cursor = nextUrl.searchParams.get('cursor')

    await fetchModels({ cursor }, true)
  }

  /**
   * Clear current model
   */
  const clearCurrentModel = () => {
    currentModel.value = null
  }

  /**
   * Clear error
   */
  const clearError = () => {
    error.value = null
  }

  /**
   * Reset store state
   */
  const reset = () => {
    models.value = []
    currentModel.value = null
    loading.value = false
    error.value = null
    pagination.value = {
      next: null,
      previous: null,
    }
  }

  return {
    // State
    models,
    currentModel,
    loading,
    error,
    pagination,

    // Getters
    hasMore,
    modelCount,

    // Actions
    fetchModels,
    fetchModelDetail,
    createModel,
    deleteModel,
    loadMore,
    clearCurrentModel,
    clearError,
    reset,
  }
})
