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
          message: 'Vincent님이 회원님의 "Sunset Dreams" 게시물을 좋아합니다.',
          related_id: 1,
          is_read: false,
          created_at: new Date(Date.now() - 300000).toISOString(), // 5 minutes ago
          user: {
            username: 'Vincent',
            avatar: 'https://i.pravatar.cc/150?img=12',
          },
          thumbnail: 'https://images.unsplash.com/photo-1579783902614-a3fb3927b6a5?w=150&h=150&fit=crop',
        },
        {
          id: 2,
          notification_type: 'image_commented',
          message: 'Artist님이 회원님의 "Digital Art Collection" 게시물에 댓글을 남겼습니다: "정말 멋진 작품이네요!"',
          related_id: 1,
          is_read: false,
          created_at: new Date(Date.now() - 1800000).toISOString(), // 30 minutes ago
          user: {
            username: 'Artist',
            avatar: 'https://i.pravatar.cc/150?img=33',
          },
          thumbnail: 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=150&h=150&fit=crop',
        },
        {
          id: 3,
          notification_type: 'model_training_completed',
          message: '"Watercolor Dreams" 스타일 학습이 완료되었습니다. 이제 이미지 생성에 사용할 수 있습니다.',
          related_id: 1,
          is_read: true,
          created_at: new Date(Date.now() - 3600000).toISOString(), // 1 hour ago
          thumbnail: 'https://images.unsplash.com/photo-1547891654-e66ed7ebb968?w=150&h=150&fit=crop',
        },
        {
          id: 4,
          notification_type: 'image_generation_completed',
          message: '"Cyberpunk City" 이미지 생성이 완료되었습니다. 지금 확인해보세요!',
          related_id: 2,
          is_read: true,
          created_at: new Date(Date.now() - 7200000).toISOString(), // 2 hours ago
          thumbnail: 'https://images.unsplash.com/photo-1620641788421-7a1c342ea42e?w=150&h=150&fit=crop',
        },
        {
          id: 5,
          notification_type: 'new_follower',
          message: 'ArtLover님이 회원님을 팔로우하기 시작했습니다.',
          related_id: 3,
          is_read: true,
          created_at: new Date(Date.now() - 86400000).toISOString(), // 1 day ago
          user: {
            username: 'ArtLover',
            avatar: 'https://i.pravatar.cc/150?img=25',
          },
        },
        {
          id: 6,
          notification_type: 'model_training_failed',
          message: '"Abstract Patterns" 스타일 학습이 실패했습니다. 이미지를 다시 확인해주세요.',
          related_id: 4,
          is_read: true,
          created_at: new Date(Date.now() - 172800000).toISOString(), // 2 days ago
          thumbnail: 'https://images.unsplash.com/photo-1561214115-f2f134cc4912?w=150&h=150&fit=crop',
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
