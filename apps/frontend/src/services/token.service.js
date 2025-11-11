/**
 * Token Service
 *
 * Handles token operations including balance check, purchase, and transaction history.
 */
import apiClient from './api'

/**
 * Get current user's token balance
 *
 * @returns {Promise<Object>} Object with balance property
 */
export async function getBalance() {
  const response = await apiClient.get('/api/tokens/balance/')
  return response.data
}

/**
 * Purchase tokens
 *
 * @param {Object} data - Purchase data
 * @param {number} data.amount - Amount of tokens to purchase (100-1,000,000, multiples of 100)
 * @param {string} data.payment_method - Payment method (card/bank_transfer/paypal)
 * @returns {Promise<Object>} New balance and transaction details
 */
export async function purchaseTokens(data) {
  const response = await apiClient.post('/api/tokens/purchase/', data)
  return response.data
}

/**
 * Get token transaction history
 *
 * @param {Object} params - Query parameters
 * @param {string} params.cursor - Pagination cursor (optional)
 * @param {number} params.limit - Number of results per page (default: 20)
 * @param {string} params.type - Filter by transaction type (consume/purchase/earn/refund/transfer/commission)
 * @returns {Promise<Object>} Paginated list of transactions with next/previous cursors
 */
export async function getTransactions(params = {}) {
  const response = await apiClient.get('/api/tokens/transactions/', { params })
  return response.data
}

export default {
  getBalance,
  purchaseTokens,
  getTransactions,
}
