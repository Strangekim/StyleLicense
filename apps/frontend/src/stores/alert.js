import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAlertStore = defineStore('alert', () => {
  // State
  const isVisible = ref(false)
  const title = ref('')
  const message = ref('')
  const type = ref('info') // 'info', 'warning', 'error', 'success'
  const confirmText = ref('')
  const cancelText = ref('')
  const onConfirm = ref(null)
  const onCancel = ref(null)
  const showCancel = ref(true)

  // Actions
  function show(options) {
    title.value = options.title || ''
    message.value = options.message || ''
    type.value = options.type || 'info'
    confirmText.value = options.confirmText || 'OK'
    cancelText.value = options.cancelText || 'Cancel'
    onConfirm.value = options.onConfirm || null
    onCancel.value = options.onCancel || null
    showCancel.value = options.showCancel !== false
    isVisible.value = true
  }

  function hide() {
    isVisible.value = false
    // Reset after animation
    setTimeout(() => {
      title.value = ''
      message.value = ''
      type.value = 'info'
      confirmText.value = ''
      cancelText.value = ''
      onConfirm.value = null
      onCancel.value = null
      showCancel.value = true
    }, 300)
  }

  function confirm() {
    if (onConfirm.value) {
      onConfirm.value()
    }
    hide()
  }

  function cancel() {
    if (onCancel.value) {
      onCancel.value()
    }
    hide()
  }

  return {
    // State
    isVisible,
    title,
    message,
    type,
    confirmText,
    cancelText,
    showCancel,
    // Actions
    show,
    hide,
    confirm,
    cancel,
  }
})
