/**
 * ProgressIndicator Component
 *
 * Displays generation progress with status transitions:
 * queued → processing → completed/failed
 */
<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true,
    validator: (value) => ['queued', 'processing', 'completed', 'failed'].includes(value),
  },
  showLabel: {
    type: Boolean,
    default: true,
  },
  size: {
    type: String,
    default: 'md', // 'sm', 'md', 'lg'
    validator: (value) => ['sm', 'md', 'lg'].includes(value),
  },
})

// Status configuration
const statusConfig = computed(() => {
  const configs = {
    queued: {
      label: 'Queued',
      color: 'text-yellow-600',
      bgColor: 'bg-yellow-50',
      borderColor: 'border-yellow-200',
      icon: 'clock',
      progress: 0,
    },
    processing: {
      label: 'Processing',
      color: 'text-blue-600',
      bgColor: 'bg-blue-50',
      borderColor: 'border-blue-200',
      icon: 'spinner',
      progress: 50,
    },
    completed: {
      label: 'Completed',
      color: 'text-green-600',
      bgColor: 'bg-green-50',
      borderColor: 'border-green-200',
      icon: 'check',
      progress: 100,
    },
    failed: {
      label: 'Failed',
      color: 'text-red-600',
      bgColor: 'bg-red-50',
      borderColor: 'border-red-200',
      icon: 'error',
      progress: 100,
    },
  }
  return configs[props.status] || configs.queued
})

// Size configuration
const sizeConfig = computed(() => {
  const sizes = {
    sm: {
      icon: 'w-4 h-4',
      text: 'text-xs',
      padding: 'px-2 py-1',
    },
    md: {
      icon: 'w-5 h-5',
      text: 'text-sm',
      padding: 'px-3 py-1.5',
    },
    lg: {
      icon: 'w-6 h-6',
      text: 'text-base',
      padding: 'px-4 py-2',
    },
  }
  return sizes[props.size]
})
</script>

<template>
  <div
    class="inline-flex items-center gap-2 rounded-full border"
    :class="[
      statusConfig.bgColor,
      statusConfig.borderColor,
      statusConfig.color,
      sizeConfig.padding,
    ]"
  >
    <!-- Icon -->
    <div :class="sizeConfig.icon">
      <!-- Queued - Clock -->
      <svg
        v-if="statusConfig.icon === 'clock'"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>

      <!-- Processing - Spinner -->
      <svg
        v-else-if="statusConfig.icon === 'spinner'"
        class="animate-spin"
        fill="none"
        viewBox="0 0 24 24"
      >
        <circle
          class="opacity-25"
          cx="12"
          cy="12"
          r="10"
          stroke="currentColor"
          stroke-width="4"
        ></circle>
        <path
          class="opacity-75"
          fill="currentColor"
          d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
        ></path>
      </svg>

      <!-- Completed - Check -->
      <svg
        v-else-if="statusConfig.icon === 'check'"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M5 13l4 4L19 7"
        />
      </svg>

      <!-- Failed - Error -->
      <svg
        v-else-if="statusConfig.icon === 'error'"
        fill="none"
        stroke="currentColor"
        viewBox="0 0 24 24"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z"
        />
      </svg>
    </div>

    <!-- Label -->
    <span v-if="showLabel" :class="['font-medium', sizeConfig.text]">
      {{ statusConfig.label }}
    </span>
  </div>
</template>
