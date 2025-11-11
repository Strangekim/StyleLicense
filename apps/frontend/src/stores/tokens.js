/**
 * Tokens Store
 *
 * Manages token state including balance, purchase, and transaction history.
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import tokenService from '@/services/token.service'
import { useAuthStore } from './auth'

export const useTokenStore = defineStore('tokens', () => {
  // State
  const balance = ref(0)
  const transactions = ref([])
  const loading = ref(false)
  const error = ref(null)
  const pagination = ref({
    next: null,
    previous: null,
  })

  // Getters
  const hasMore = computed(() => pagination.value.next !== null)
  const transactionCount = computed(() => transactions.value.length)

  /**
   * Fetch token balance
   */
  const fetchBalance = async () => {
    try {
      loading.value = true
      error.value = null

      const response = await tokenService.getBalance()

      if (response.success) {
        balance.value = response.data.balance

        // Also update auth store user balance
        const authStore = useAuthStore()
        if (authStore.user) {
          authStore.user.token_balance = response.data.balance
        }
      }
    } catch (err) {
      error.value = err.response?.data?.error?.message || 'Failed to fetch balance'
      console.error('Error fetching balance:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Purchase tokens
   * @param {Object} data - Purchase data (amount, payment_method)
   * @returns {Object} New balance and transaction details
   */
  const purchaseTokens = async (data) => {
    try {
      loading.value = true
      error.value = null

      const response = await tokenService.purchaseTokens(data)

      if (response.success) {
        balance.value = response.data.balance

        // Update auth store user balance
        const authStore = useAuthStore()
        if (authStore.user) {
          authStore.user.token_balance = response.data.balance
        }

        // Add transaction to beginning of list if we're on first page
        if (response.data.transaction && !pagination.value.previous) {
          transactions.value.unshift(response.data.transaction)
        }

        return response.data
      }
    } catch (err) {
      error.value = err.response?.data?.error?.message || 'Failed to purchase tokens'
      console.error('Error purchasing tokens:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  /**
   * Fetch transaction history
   * @param {Object} params - Query parameters (type, cursor, limit)
   * @param {boolean} append - Whether to append to existing list
   */
  const fetchTransactions = async (params = {}, append = false) => {
    try {
      loading.value = true
      error.value = null

      const response = await tokenService.getTransactions(params)

      if (response.success) {
        const data = response.data

        if (append) {
          transactions.value.push(...data.results)
        } else {
          transactions.value = data.results
        }

        pagination.value = {
          next: data.next,
          previous: data.previous,
        }
      }
    } catch (err) {
      error.value = err.response?.data?.error?.message || 'Failed to fetch transactions'
      console.error('Error fetching transactions:', err)
    } finally {
      loading.value = false
    }
  }

  /**
   * Load more transactions (for infinite scroll)
   */
  const loadMore = async () => {
    if (!hasMore.value || loading.value) return

    // Extract cursor from next URL
    const nextUrl = new URL(pagination.value.next)
    const cursor = nextUrl.searchParams.get('cursor')

    await fetchTransactions({ cursor }, true)
  }

  /**
   * Update balance locally (for optimistic updates)
   * @param {number} amount - Amount to add/subtract (can be negative)
   */
  const updateBalance = (amount) => {
    balance.value += amount

    // Update auth store
    const authStore = useAuthStore()
    if (authStore.user) {
      authStore.user.token_balance += amount
    }
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
    balance.value = 0
    transactions.value = []
    loading.value = false
    error.value = null
    pagination.value = {
      next: null,
      previous: null,
    }
  }

  return {
    // State
    balance,
    transactions,
    loading,
    error,
    pagination,

    // Getters
    hasMore,
    transactionCount,

    // Actions
    fetchBalance,
    purchaseTokens,
    fetchTransactions,
    loadMore,
    updateBalance,
    clearError,
    reset,
  }
})
