/**
 * Generations Store (Image Generation)
 *
 * Manages image generation state including generating images, checking status,
 * and managing generation queue.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import generationService from '@/services/generation.service'

export const useGenerationStore = defineStore('generations', () => {
  // State
  const generations = ref([])
  const currentGeneration = ref(null)
  const queue = ref([]) // Active generations being polled
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({
    next: null,
    previous: null,
  })

  // Polling intervals
  const pollingIntervals = ref(new Map())

  // Getters
  const hasMore = computed(() => pagination.value.next !== null)
  const generationCount = computed(() => generations.value.length)
  const queueCount = computed(() => queue.value.length)
  const hasActiveGenerations = computed(() => queue.value.length > 0)

  /**
   * Generate image with style model
   * @param {Object} data - Generation data (style_id, prompt, aspect_ratio, seed)
   * @returns {Object} Generation result with generation_id and status
   */
  const generateImage = async (data) => {
    try {
      loading.value = true
      error.value = null

      const response = await generationService.generateImage(data)

      if (response.success) {
        const generation = response.data

        // Add to queue for status polling
        queue.value.unshift(generation)

        // Add to generations list
        generations.value.unshift(generation)

        // Start polling for this generation
        startPolling(generation.id)

        return generation
      }
    } catch (err) {
      error.value = err.response?.data?.error?.message || 'Failed to generate image'
      console.error('Error generating image:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Check generation status
   * @param {number} id - Generation ID
   * @returns {Object} Generation status
   */
  const checkStatus = async (id) => {
    try {
      const response = await generationService.getGenerationStatus(id)

      if (response.success) {
        const status = response.data

        // Update generation in queue
        const queueIndex = queue.value.findIndex((g) => g.id === id)
        if (queueIndex !== -1) {
          queue.value[queueIndex] = { ...queue.value[queueIndex], ...status }

          // Remove from queue if completed or failed
          if (status.status === 'completed' || status.status === 'failed') {
            queue.value.splice(queueIndex, 1)
            stopPolling(id)
          }
        }

        // Update generation in list
        const listIndex = generations.value.findIndex((g) => g.id === id)
        if (listIndex !== -1) {
          generations.value[listIndex] = { ...generations.value[listIndex], ...status }
        }

        // Update current generation if it's the one being checked
        if (currentGeneration.value?.id === id) {
          currentGeneration.value = { ...currentGeneration.value, ...status }
        }

        return status
      }
    } catch (err) {
      console.error('Error checking generation status:', err)
      throw err
    }
  }

  /**
   * Start polling for generation status
   * @param {number} id - Generation ID
   * @param {number} interval - Polling interval in ms (default: 5000)
   */
  const startPolling = (id, interval = 5000) => {
    // Stop existing polling if any
    stopPolling(id)

    // Start new polling interval
    const intervalId = setInterval(async () => {
      try {
        await checkStatus(id)
      } catch (err) {
        console.error(`Polling error for generation ${id}:`, err)
        stopPolling(id)
      }
    }, interval)

    pollingIntervals.value.set(id, intervalId)
  }

  /**
   * Stop polling for generation status
   * @param {number} id - Generation ID
   */
  const stopPolling = (id) => {
    const intervalId = pollingIntervals.value.get(id)
    if (intervalId) {
      clearInterval(intervalId)
      pollingIntervals.value.delete(id)
    }
  }

  /**
   * Stop all polling
   */
  const stopAllPolling = () => {
    pollingIntervals.value.forEach((intervalId) => clearInterval(intervalId))
    pollingIntervals.value.clear()
  }

  /**
   * Fetch generation history
   * @param {Object} params - Query parameters (status, cursor, limit)
   * @param {boolean} append - Whether to append to existing list
   */
  const fetchGenerations = async (params = {}, append = false) => {
    try {
      loading.value = true
      error.value = null

      const response = await generationService.listGenerations(params)

      if (response.success) {
        const data = response.data

        if (append) {
          generations.value.push(...data.results)
        } else {
          generations.value = data.results
        }

        pagination.value = {
          next: data.next,
          previous: data.previous,
        }
      }
    } catch (err) {
      error.value = err.response?.data?.error?.message || 'Failed to fetch generations'
      console.error('Error fetching generations:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch generation detail
   * @param {number} id - Generation ID
   */
  const fetchGenerationDetail = async (id) => {
    try {
      loading.value = true
      error.value = null

      const response = await generationService.getGenerationDetail(id)

      if (response.success) {
        currentGeneration.value = response.data
      }
    } catch (err) {
      error.value = err.response?.data?.error?.message || 'Failed to fetch generation detail'
      console.error('Error fetching generation detail:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Load more generations (for infinite scroll)
   */
  const loadMore = async () => {
    if (!hasMore.value || loading.value) return

    // Extract cursor from next URL
    const nextUrl = new URL(pagination.value.next)
    const cursor = nextUrl.searchParams.get('cursor')

    await fetchGenerations({ cursor }, true)
  }

  /**
   * Clear current generation
   */
  const clearCurrentGeneration = () => {
    currentGeneration.value = null
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
    stopAllPolling()
    generations.value = []
    currentGeneration.value = null
    queue.value = []
    loading.value = false
    error.value = null
    pagination.value = {
      next: null,
      previous: null,
    }
  }

  return {
    // State
    generations,
    currentGeneration,
    queue,
    loading,
    error,
    pagination,

    // Getters
    hasMore,
    generationCount,
    queueCount,
    hasActiveGenerations,

    // Actions
    generateImage,
    checkStatus,
    startPolling,
    stopPolling,
    stopAllPolling,
    fetchGenerations,
    fetchGenerationDetail,
    loadMore,
    clearCurrentGeneration,
    clearError,
    reset,
  }
})
