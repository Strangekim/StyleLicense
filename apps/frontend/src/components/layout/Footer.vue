<template>
  <footer class="bg-neutral-50 border-t border-neutral-200">
    <div class="container mx-auto px-4 py-8">
      <div class="grid grid-cols-1 md:grid-cols-4 gap-8">
        <!-- Brand -->
        <div class="col-span-1">
          <div class="flex items-center gap-2 text-xl font-bold text-primary-600 mb-4">
            <span>🎨</span>
            <span>Style License</span>
          </div>
          <p class="text-sm text-neutral-600">
            AI-powered art style licensing platform for creators.
          </p>
        </div>

        <!-- Platform Links -->
        <div class="col-span-1">
          <h3 class="font-semibold text-neutral-900 mb-3">Platform</h3>
          <ul class="space-y-2">
            <li>
              <router-link to="/" class="text-sm text-neutral-600 hover:text-primary-600 transition-colors">
                Marketplace
              </router-link>
            </li>
            <li>
              <router-link to="/generate" class="text-sm text-neutral-600 hover:text-primary-600 transition-colors">
                Generate
              </router-link>
            </li>
            <li>
              <router-link to="/styles/create" class="text-sm text-neutral-600 hover:text-primary-600 transition-colors">
                Create Style
              </router-link>
            </li>
          </ul>
        </div>

        <!-- Resources -->
        <div class="col-span-1">
          <h3 class="font-semibold text-neutral-900 mb-3">Resources</h3>
          <ul class="space-y-2">
            <li>
              <a href="#" class="text-sm text-neutral-600 hover:text-primary-600 transition-colors">
                Documentation
              </a>
            </li>
            <li>
              <a href="#" class="text-sm text-neutral-600 hover:text-primary-600 transition-colors">
                API Reference
              </a>
            </li>
            <li>
              <a href="#" class="text-sm text-neutral-600 hover:text-primary-600 transition-colors">
                Support
              </a>
            </li>
          </ul>
        </div>

        <!-- Legal -->
        <div class="col-span-1">
          <h3 class="font-semibold text-neutral-900 mb-3">Legal</h3>
          <ul class="space-y-2">
            <li>
              <a href="#" class="text-sm text-neutral-600 hover:text-primary-600 transition-colors">
                Terms of Service
              </a>
            </li>
            <li>
              <a href="#" class="text-sm text-neutral-600 hover:text-primary-600 transition-colors">
                Privacy Policy
              </a>
            </li>
            <li>
              <a href="#" class="text-sm text-neutral-600 hover:text-primary-600 transition-colors">
                License Agreement
              </a>
            </li>
          </ul>
        </div>
      </div>

      <!-- Copyright -->
      <div class="mt-8 pt-8 border-t border-neutral-200">
        <p class="text-sm text-center text-neutral-600">
          © {{ currentYear }} Style License. All rights reserved.
        </p>
      </div>
    </div>
  </footer>
</template>

<script setup>
import { computed } from 'vue'

const currentYear = computed(() => new Date().getFullYear())
</script>
