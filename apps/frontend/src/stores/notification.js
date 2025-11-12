/**
 * Notification store for managing user notifications
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getNotifications,
  markAsRead,
  markAllAsRead,
} from '@/services/notification.service'

export const useNotificationStore = defineStore('notification', () => {
  // State
  const notifications = ref([])
  const unreadCount = ref(0)
  const loading = ref(false)
  const error = ref(null)

  // Computed
  const hasUnread = computed(() => unreadCount.value > 0)

  // Actions
  async function fetchNotifications(params = {}) {
    loading.value = true
    error.value = null

    try {
      const data = await getNotifications(params)
      notifications.value = data.results || []
      unreadCount.value = data.unread_count || 0
      return data
    } catch (err) {
      error.value = err.message || 'Failed to fetch notifications'
      console.error('Failed to fetch notifications:', err)
      throw err
    } finally {
      loading.value = false
    }
  }

  async function markNotificationAsRead(notificationId) {
    try {
      await markAsRead(notificationId)

      // Update local state
      const notification = notifications.value.find((n) => n.id === notificationId)
      if (notification && !notification.is_read) {
        notification.is_read = true
        unreadCount.value = Math.max(0, unreadCount.value - 1)
      }
    } catch (err) {
      console.error('Failed to mark notification as read:', err)
      throw err
    }
  }

  async function markAllNotificationsAsRead() {
    try {
      await markAllAsRead()

      // Update local state
      notifications.value.forEach((n) => {
        n.is_read = true
      })
      unreadCount.value = 0
    } catch (err) {
      console.error('Failed to mark all notifications as read:', err)
      throw err
    }
  }

  function clearNotifications() {
    notifications.value = []
    unreadCount.value = 0
    error.value = null
  }

  return {
    // State
    notifications,
    unreadCount,
    loading,
    error,
    // Computed
    hasUnread,
    // Actions
    fetchNotifications,
    markNotificationAsRead,
    markAllNotificationsAsRead,
    clearNotifications,
  }
})
