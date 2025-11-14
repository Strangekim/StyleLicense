import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

/**
 * Router Configuration with Code Splitting
 *
 * All routes use lazy loading (dynamic imports) to split the bundle
 * into smaller chunks that are loaded on-demand. This improves initial
 * page load performance by reducing the main bundle size.
 *
 * Vite will automatically create separate chunks for each route component.
 */

const routes = [
  {
    path: '/',
    name: 'Home',
    component: () => import('@/pages/Home.vue'),
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/auth/Login.vue'),
    meta: { requiresGuest: true }, // Only accessible when not authenticated
  },
  {
    path: '/auth/google/callback',
    name: 'GoogleCallback',
    component: () => import('@/pages/auth/GoogleCallback.vue'),
  },
  // Marketplace routes (public)
  {
    path: '/marketplace',
    name: 'Marketplace',
    component: () => import('@/pages/marketplace/ModelMarketplace.vue'),
  },
  {
    path: '/models/:id',
    name: 'ModelDetail',
    component: () => import('@/pages/marketplace/ModelDetail.vue'),
  },
  // Generation routes (authenticated users)
  {
    path: '/generate',
    name: 'Generate',
    component: () => import('@/pages/generate/ImageGeneration.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/generate/history',
    name: 'GenerationHistory',
    component: () => import('@/pages/generate/GenerationHistory.vue'),
    meta: { requiresAuth: true },
  },
  // Community routes (public)
  {
    path: '/community',
    name: 'Community',
    component: () => import('@/pages/community/Community.vue'),
  },
  // Artist routes (protected)
  {
    path: '/styles/create',
    name: 'StyleCreate',
    component: () => import('@/pages/artist/StyleCreate.vue'),
    meta: { requiresAuth: true, requiresArtist: true },
  },
  // 404 Not Found - must be last
  {
    path: '/:pathMatch(.*)*',
    name: 'NotFound',
    component: () => import('@/pages/NotFound.vue'),
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Only fetch user if the route requires authentication or if we need to check auth status
  const needsAuthCheck = to.meta.requiresAuth || to.meta.requiresArtist || to.meta.requiresGuest

  if (needsAuthCheck && !authStore.user && !authStore.loading) {
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
