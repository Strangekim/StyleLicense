/**
 * Alert Component
 *
 * Global alert/dialog component for displaying messages to users.
 * Supports different types (info, warning, error, success) with customizable buttons.
 */
<script setup>
import { computed } from 'vue'
import { useAlertStore } from '@/stores/alert'
import Button from './Button.vue'

const alertStore = useAlertStore()

// Computed: Icon based on type
const iconConfig = computed(() => {
  const configs = {
    info: {
      bgColor: 'bg-blue-100',
      iconColor: 'text-blue-600',
      path: 'M13 16h-1v-4h-1m1-4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z'
    },
    warning: {
      bgColor: 'bg-yellow-100',
      iconColor: 'text-yellow-600',
      path: 'M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z'
    },
    error: {
      bgColor: 'bg-red-100',
      iconColor: 'text-red-600',
      path: 'M10 14l2-2m0 0l2-2m-2 2l-2-2m2 2l2 2m7-2a9 9 0 11-18 0 9 9 0 0118 0z'
    },
    success: {
      bgColor: 'bg-green-100',
      iconColor: 'text-green-600',
      path: 'M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z'
    }
  }
  return configs[alertStore.type] || configs.info
})
</script>

<template>
  <!-- Backdrop -->
  <Transition name="fade">
    <div
      v-if="alertStore.isVisible"
      class="fixed inset-0 bg-black bg-opacity-50 z-50 flex items-center justify-center p-4"
      @click="alertStore.cancel"
    >
      <!-- Alert Dialog -->
      <Transition name="scale">
        <div
          v-if="alertStore.isVisible"
          class="bg-white rounded-2xl shadow-2xl max-w-md w-full overflow-hidden"
          @click.stop
        >
          <!-- Header with Icon -->
          <div class="px-6 pt-6 pb-4">
            <div class="flex items-start gap-4">
              <!-- Icon -->
              <div
                :class="[
                  'flex-shrink-0 w-12 h-12 rounded-full flex items-center justify-center',
                  iconConfig.bgColor
                ]"
              >
                <svg
                  :class="['w-6 h-6', iconConfig.iconColor]"
                  fill="none"
                  stroke="currentColor"
                  viewBox="0 0 24 24"
                >
                  <path
                    stroke-linecap="round"
                    stroke-linejoin="round"
                    stroke-width="2"
                    :d="iconConfig.path"
                  />
                </svg>
              </div>

              <!-- Title and Message -->
              <div class="flex-1 min-w-0">
                <h3 v-if="alertStore.title" class="text-lg font-semibold text-neutral-900 mb-1">
                  {{ alertStore.title }}
                </h3>
                <p class="text-neutral-600 text-sm leading-relaxed">
                  {{ alertStore.message }}
                </p>
              </div>
            </div>
          </div>

          <!-- Actions -->
          <div class="px-6 py-4 bg-neutral-50 flex gap-3 justify-end">
            <Button
              v-if="alertStore.showCancel"
              variant="outline"
              @click="alertStore.cancel"
            >
              {{ alertStore.cancelText }}
            </Button>
            <Button
              variant="primary"
              @click="alertStore.confirm"
            >
              {{ alertStore.confirmText }}
            </Button>
          </div>
        </div>
      </Transition>
    </div>
  </Transition>
</template>

<style scoped>
/* Fade transition for backdrop */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.2s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* Scale transition for dialog */
.scale-enter-active,
.scale-leave-active {
  transition: all 0.3s ease;
}

.scale-enter-from,
.scale-leave-to {
  opacity: 0;
  transform: scale(0.95);
}
</style>
