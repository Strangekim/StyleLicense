<template>
  <div class="min-h-screen flex flex-col bg-neutral-50">
    <!-- Header -->
    <Header />

    <!-- Main Content -->
    <main class="flex-1">
      <slot />
    </main>

    <!-- Footer -->
    <Footer />
  </div>
</template>

<script setup>
import Header from './Header.vue'
import Footer from './Footer.vue'
</script>
