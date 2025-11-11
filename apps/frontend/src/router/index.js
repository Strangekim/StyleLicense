import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Pages
import Home from '@/pages/Home.vue'
import Login from '@/pages/auth/Login.vue'
import GoogleCallback from '@/pages/auth/GoogleCallback.vue'
import ModelMarketplace from '@/pages/marketplace/ModelMarketplace.vue'
import ModelDetail from '@/pages/marketplace/ModelDetail.vue'

const routes = [
  {
    path: '/',
    name: 'Home',
    component: Home,
  },
  {
    path: '/login',
    name: 'Login',
    component: Login,
    meta: { requiresGuest: true }, // Only accessible when not authenticated
  },
  {
    path: '/auth/google/callback',
    name: 'GoogleCallback',
    component: GoogleCallback,
  },
  // Marketplace routes (public)
  {
    path: '/marketplace',
    name: 'Marketplace',
    component: ModelMarketplace,
  },
  {
    path: '/models/:id',
    name: 'ModelDetail',
    component: ModelDetail,
  },
  // Artist routes (protected)
  {
    path: '/styles/create',
    name: 'StyleCreate',
    component: () => import('@/pages/artist/StyleCreate.vue'),
    meta: { requiresAuth: true, requiresArtist: true },
  },
  // Generation routes (to be added later)
  // {
  //   path: '/generate',
  //   name: 'Generate',
  //   component: () => import('@/pages/generate/ImageGeneration.vue'),
  //   meta: { requiresAuth: true },
  // },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Try to fetch user if not already loaded
  if (!authStore.user && !authStore.loading) {
    try {
      await authStore.fetchCurrentUser()
    } catch (error) {
      // User not authenticated, continue with navigation
      console.log('User not authenticated')
    }
  }

  // Check if route requires authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Redirect to login with return URL
    next({
      name: 'Login',
      query: { returnUrl: to.fullPath },
    })
    return
  }

  // Check if route requires artist role
  if (to.meta.requiresArtist && !authStore.isArtist) {
    // Redirect to home with error message
    console.error('This page is only accessible to artists')
    next({ name: 'Home' })
    return
  }

  // Check if route requires guest (not authenticated)
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    // Redirect authenticated users away from login page
    next({ name: 'Home' })
    return
  }

  // Allow navigation
  next()
})

export default router
