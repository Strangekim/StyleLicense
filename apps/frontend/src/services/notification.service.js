/**
 * Notification service for fetching and managing notifications
 */
import api from './api'

/**
 * Get notifications for current user
 * @param {Object} params - Query parameters
 * @param {number} params.page - Page number
 * @param {boolean} params.unread_only - Filter unread only
 * @returns {Promise<Object>} - Notification list with unread_count
 */
export async function getNotifications(params = {}) {
  const response = await api.get('/api/notifications/', { params })
  return response.data
}

/**
 * Mark a notification as read
 * @param {number} notificationId - Notification ID
 * @returns {Promise<Object>} - Updated notification
 */
export async function markAsRead(notificationId) {
  const response = await api.patch(`/api/notifications/${notificationId}/read/`)
  return response.data
}

/**
 * Mark all notifications as read
 * @returns {Promise<Object>} - Response with updated count
 */
export async function markAllAsRead() {
  const response = await api.post('/api/notifications/mark-all-read/')
  return response.data
}
