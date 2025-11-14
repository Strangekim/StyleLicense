<template>
  <div class="min-h-screen flex items-center justify-center bg-neutral-50">
    <div class="text-center px-4">
      <h1 class="text-9xl font-bold text-primary-600">404</h1>
      <h2 class="text-3xl font-semibold text-neutral-900 mt-4">Page Not Found</h2>
      <p class="text-neutral-600 mt-2 max-w-md">
        The page you're looking for doesn't exist or has been moved.
      </p>
      <router-link
        to="/"
        class="inline-block mt-8 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors font-medium"
      >
        Back to Home
      </router-link>
    </div>
  </div>
</template>

<script setup>
// 404 Not Found page
</script>
