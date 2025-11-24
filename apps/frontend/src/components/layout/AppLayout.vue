<template>
  <div class="min-h-screen flex flex-col bg-white pb-16">
    <!-- Header -->
    <Header />

    <!-- Main Content -->
    <main class="flex-1">
      <slot />
    </main>

    <!-- Bottom Navigation -->
    <BottomNav />
  </div>
</template>

<script setup>
import Header from './Header.vue'
import BottomNav from './BottomNav.vue'
</script>
