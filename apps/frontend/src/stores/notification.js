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
      console.warn('Failed to fetch notifications from API, using mock data:', err)

      // Mock data for development
      notifications.value = [
        {
          id: 1,
          notification_type: 'image_liked',
          message: 'Vincent님이 회원님의 게시물을 좋아합니다.',
          related_id: 1,
          is_read: false,
          created_at: new Date(Date.now() - 300000).toISOString(), // 5 minutes ago
        },
        {
          id: 2,
          notification_type: 'image_commented',
          message: 'Artist님이 회원님의 게시물에 댓글을 남겼습니다: "정말 멋진 작품이네요!"',
          related_id: 1,
          is_read: false,
          created_at: new Date(Date.now() - 1800000).toISOString(), // 30 minutes ago
        },
        {
          id: 3,
          notification_type: 'model_training_completed',
          message: '스타일 학습이 완료되었습니다.',
          related_id: 1,
          is_read: true,
          created_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
        },
        {
          id: 4,
          notification_type: 'image_generation_completed',
          message: '이미지 생성이 완료되었습니다.',
          related_id: 2,
          is_read: true,
          created_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
        },
        {
          id: 5,
          notification_type: 'new_follower',
          message: 'ArtLover님이 회원님을 팔로우하기 시작했습니다.',
          related_id: 3,
          is_read: true,
          created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
        },
      ]
      unreadCount.value = notifications.value.filter(n => !n.is_read).length

      return {
        results: notifications.value,
        unread_count: unreadCount.value
      }
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
