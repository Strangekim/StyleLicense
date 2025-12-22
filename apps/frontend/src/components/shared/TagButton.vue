<template>
  <button
    class="inline-flex items-center px-3 py-1.5 rounded-full text-sm font-medium bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 transition-colors"
    :class="{ 'bg-blue-50 border-blue-500 text-blue-700': selected }"
    @click="$emit('click')"
  >
    <svg class="w-4 h-4 mr-1.5" viewBox="0 0 20 20">
      <defs>
        <linearGradient id="tagButtonGradient" x1="0%" y1="0%" x2="100%" y2="0%">
          <stop offset="0%" style="stop-color:#fb923c;stop-opacity:1" />
          <stop offset="50%" style="stop-color:#facc15;stop-opacity:1" />
          <stop offset="100%" style="stop-color:#4ade80;stop-opacity:1" />
        </linearGradient>
      </defs>
      <path
        fill="url(#tagButtonGradient)"
        fill-rule="evenodd"
        d="M17.707 9.293a1 1 0 010 1.414l-7 7a1 1 0 01-1.414 0l-7-7A.997.997 0 012 10V5a3 3 0 013-3h5c.256 0 .512.098.707.293l7 7zM5 6a1 1 0 100-2 1 1 0 000 2z"
        clip-rule="evenodd"
      />
    </svg>
    <slot>{{ label }}</slot>
  </button>
</template>

<script setup>
defineProps({
  label: {
    type: String,
    default: 'TAG',
  },
  selected: {
    type: Boolean,
    default: false,
  },
})

defineEmits(['click'])
</script>
