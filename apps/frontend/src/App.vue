<script setup>
import { onMounted } from 'vue'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()

// Initialize auth from localStorage on app mount
onMounted(async () => {
  await authStore.initAuth()
})
</script>

<template>
  <router-view />
</template>
