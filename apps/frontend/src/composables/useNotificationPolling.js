/**
 * Composable for polling notifications every 5 seconds
 */
import { onMounted, onUnmounted, ref } from 'vue'
import { useNotificationStore } from '@/stores/notification'
import { useAuthStore } from '@/stores/auth'

/**
 * Start polling notifications when user is authenticated
 * @param {number} intervalMs - Polling interval in milliseconds (default: 5000)
 * @returns {Object} - { isPolling, startPolling, stopPolling }
 */
export function useNotificationPolling(intervalMs = 5000) {
  const notificationStore = useNotificationStore()
  const authStore = useAuthStore()
  const intervalId = ref(null)
  const isPolling = ref(false)

  function startPolling() {
    // Only poll if user is authenticated
    if (!authStore.isAuthenticated) {
      return
    }

    // Don't start if already polling
    if (isPolling.value) {
      return
    }

    // Fetch immediately
    notificationStore.fetchNotifications({ unread_only: false }).catch((err) => {
      console.error('Failed to fetch notifications:', err)
    })

    // Then poll every interval
    intervalId.value = setInterval(() => {
      if (authStore.isAuthenticated) {
        notificationStore.fetchNotifications({ unread_only: false }).catch((err) => {
          console.error('Failed to fetch notifications:', err)
        })
      } else {
        stopPolling()
      }
    }, intervalMs)

    isPolling.value = true
  }

  function stopPolling() {
    if (intervalId.value) {
      clearInterval(intervalId.value)
      intervalId.value = null
    }
    isPolling.value = false
  }

  // Auto-start polling when component mounts (if authenticated)
  onMounted(() => {
    if (authStore.isAuthenticated) {
      startPolling()
    }
  })

  // Auto-stop polling when component unmounts
  onUnmounted(() => {
    stopPolling()
  })

  return {
    isPolling,
    startPolling,
    stopPolling,
  }
}
