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
    component: () => import('@/pages/community/Community.vue'), // Main feed as home
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/pages/auth/Login.vue'),
    meta: { requiresGuest: true }, // Only accessible when not authenticated
  },
  {
    path: '/auth/callback',
    name: 'AuthCallback',
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
    component: () => import('@/pages/marketplace/StyleDetail.vue'),
  },
  // Legacy generate route - redirect to marketplace
  {
    path: '/generate',
    redirect: '/marketplace',
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
  {
    path: '/community/:id',
    name: 'CommunityDetail',
    component: () => import('@/pages/community/CommunityDetail.vue'),
  },
  // Profile routes (require authentication)
  {
    path: '/profile',
    name: 'Profile',
    component: () => import('@/pages/profile/Profile.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/profile/edit',
    name: 'EditProfile',
    component: () => import('@/pages/profile/EditProfile.vue'),
    meta: { requiresAuth: true },
  },
  // Notifications route (require authentication)
  {
    path: '/notifications',
    name: 'Notifications',
    component: () => import('@/pages/notifications/Notifications.vue'),
    meta: { requiresAuth: true },
  },
  // Token/Payment route (require authentication)
  {
    path: '/tokens',
    name: 'Tokens',
    component: () => import('@/pages/tokens/TokenPage.vue'),
    meta: { requiresAuth: true },
  },
  // Artist routes (require authentication)
  {
    path: '/styles/create',
    name: 'StyleCreate',
    component: () => import('@/pages/artist/StyleCreate.vue'),
    meta: { requiresAuth: true },
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

// Track if auth has been initialized to avoid redundant calls
let authInitialized = false

// Navigation guards
router.beforeEach(async (to, from, next) => {
  const authStore = useAuthStore()

  // Initialize auth state on first navigation (page load/refresh)
  if (!authInitialized) {
    authInitialized = true
    await authStore.initAuth()
  }

  // Check if route requires authentication
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    // Save the intended destination to redirect after login
    if (to.fullPath !== '/') {
      localStorage.setItem('post_login_return_url', to.fullPath)
    }
    next({ name: 'Login' })
    return
  }

  // Check if route requires artist role
  if (to.meta.requiresArtist && !authStore.isArtist) {
    console.error('This page is only accessible to artists.')
    next({ name: 'Home' }) // Or an 'Unauthorized' page
    return
  }

  // Check if a route is for guests only (like the login page)
  if (to.meta.requiresGuest && authStore.isAuthenticated) {
    next({ name: 'Home' })
    return
  }

  // Otherwise, allow navigation
  next()
})

export default router
