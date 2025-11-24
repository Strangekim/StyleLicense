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
      console.error('Failed to fetch models from API:', err)
      error.value = err.response?.data?.error?.message || 'Failed to load models'
      throw err
    } finally{
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
      console.error('Failed to fetch model detail from API:', err)
      error.value = err.response?.data?.error?.message || 'Failed to load model detail'
      throw err
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
