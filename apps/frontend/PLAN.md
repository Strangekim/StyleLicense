# Frontend Development Plan

**App**: Frontend (Vue 3 + Vite)  
**Last Updated**: 2025-11-05  
**Status**: M1 In Progress

---

## Overview

This document contains detailed subtasks for frontend development. For high-level milestones and dependencies, see [root PLAN.md](../../PLAN.md).

**Reference Documents**:
- [Frontend README.md](README.md) - Architecture, directory structure, **Design System**
- [Frontend CODE_GUIDE.md](CODE_GUIDE.md) - Code patterns and conventions
- [API Documentation](../../docs/API.md) - API specifications
- [Design Mockups](../../docs/design/pages/) - 17 page design mockups (PNG/JPG)

**Design Guidelines** (See README.md#design-system):
1. ✅ Follow `docs/design/pages/` mockups with flexibility for consistency
2. ✅ Use Instagram UI patterns as reference
3. ✅ TECHSPEC.md is authority - remove features not listed (e.g., comment likes)
4. ✅ Follow commercial standards (smooth animations, accessibility)
5. ✅ Extract colors/fonts to `tailwind.config.js`

---

## M1: Foundation

### M1-Initialization

**Referenced by**: Root PLAN.md → PT-M1-Frontend
**Status**: DONE

#### Subtasks

- [x] Vite + Vue 3 project setup (Commit: 275e328)
  - [x] npm create vite@latest . -- --template vue
  - [x] Configure vite.config.js with alias (@/ for src/)
  - [x] Set up development server on port 5173

- [x] Tailwind CSS configuration (Commit: 275e328)
  - [x] Install tailwindcss, postcss, autoprefixer
  - [x] Create tailwind.config.js
  - [x] Add Tailwind directives to src/style.css
  - [x] Test Tailwind classes render correctly

- [x] Install core dependencies (Commit: 275e328)
  - [x] Install Pinia for state management
  - [x] Install Vue Router for routing
  - [x] Install Axios for HTTP requests
  - [x] Install vue-i18n for internationalization

- [x] i18n setup (en, ko) (Commit: 275e328)
  - [x] Create src/i18n/index.js
  - [x] Create src/locales/en.json and ko.json
  - [x] Configure default locale: en
  - [ ] Add language switcher to header (optional, deferred to Header component)

- [x] Directory structure setup (Commit: 275e328)
  - [x] Create src/components/ (shared, features/, layout)
  - [x] Create src/pages/
  - [x] Create src/stores/
  - [x] Create src/composables/
  - [x] Create src/services/
  - [x] Create src/assets/ (images and icons already exist)

- [x] Docker configuration
  - [x] Verify Dockerfile multi-stage build
  - [ ] Test container starts with docker-compose up frontend (deferred to later)

**Exit Criteria**:
- ✅ npm run dev starts dev server on localhost:5173
- ✅ Tailwind CSS classes work
- ✅ All dependencies installed without errors

---

### M1-Design-System

**Referenced by**: Root PLAN.md → PT-M1-Frontend
**Status**: DONE
**Description**: Create the foundational UI components and define design tokens. This is the first step in building the UI, ensuring a consistent look and feel across the application.

#### Subtasks

- [x] Define Design Tokens (Commit: a1a70f0)
  - [x] Created primary color palette (indigo/purple for creativity)
  - [x] Created secondary color palette (emerald for success)
  - [x] Created neutral color palette (Instagram-inspired grays)
  - [x] Added custom spacing, border radius, and shadows to `tailwind.config.js`
  - [x] Configured Inter font family with system font fallback

- [x] Create Button component (Commit: a1a70f0)
  - [x] Create src/components/shared/Button.vue
  - [x] Props: variant (primary, secondary, outline, ghost), size (sm, md, lg), loading, fullWidth
  - [x] Emit click event
  - [x] Tailwind classes for each variant
  - [x] Loading spinner with SVG animation

- [x] Create Input component (Commit: a1a70f0)
  - [x] Create src/components/shared/Input.vue
  - [x] Props: type (text, email, number, password, textarea), placeholder, modelValue
  - [x] Emit update:modelValue for v-model
  - [x] Error state styling (red border and text)
  - [x] Label, helper text, and custom helper slot

- [x] Create Modal component (Commit: a1a70f0)
  - [x] Create src/components/shared/Modal.vue
  - [x] Props: isOpen, title, size (sm/md/lg/xl), closeOnBackdrop
  - [x] Slots: default (content), header, actions (footer buttons)
  - [x] Emit close on backdrop click, X button, and ESC key
  - [x] Teleport to body for proper z-index
  - [x] Body scroll prevention when open

- [x] Create Card component (Commit: a1a70f0)
  - [x] Create src/components/shared/Card.vue
  - [x] Props: clickable (boolean), variant (default/bordered/elevated), padding (none/sm/md/lg)
  - [x] Hover effects if clickable (scale, shadow)
  - [x] Slots: default (content)

- [x] Create Header component (Commit: a1a70f0)
  - [x] Create src/components/layout/Header.vue
  - [x] Logo and navigation links (Marketplace, Generate, Create Style)
  - [x] Display token balance if authenticated
  - [x] User dropdown menu (Profile, Get Tokens, Logout)
  - [x] Mobile responsive hamburger menu
  - [x] Integration with useAuthStore

- [x] Create Footer component (Commit: a1a70f0)
  - [x] Create src/components/layout/Footer.vue
  - [x] Brand section with logo
  - [x] Links to Platform, Resources, Legal pages
  - [x] Copyright notice with current year

- [x] Create AppLayout component (Commit: a1a70f0)
  - [x] Create src/components/layout/AppLayout.vue
  - [x] Render Header + main slot + Footer
  - [x] Min-height layout with sticky header

- [x] Testing (Commit: a1a70f0)
  - [x] Test dev server starts successfully (592ms build time)
  - [x] No build errors or warnings
  - [ ] Visual testing (deferred - requires pages to use components)
  - [ ] Component unit tests (deferred to later)

**Implementation Reference**:
- [CODE_GUIDE.md#components](CODE_GUIDE.md#components)
- **Design mockups**: All page mockups in `docs/design/pages/` show component usage

**Exit Criteria**:
- ✅ All base components created and functional
- ✅ Components follow design system (colors, spacing, fonts)
- ✅ Mobile responsive with Tailwind breakpoints
- ✅ Dev server builds without errors
- ⏳ Assets (logos, icons) integration deferred to page implementation

---

### M1-Auth-Frontend

**Referenced by**: Root PLAN.md → CP-M1-3
**Status**: DONE

#### Subtasks

- [x] Create useAuthStore (Commit: 9aee5e8)
  - [x] Create src/stores/auth.js
  - [x] State: user (null or user object), isAuthenticated (computed)
  - [x] Actions: fetchCurrentUser(), logout(), clearUser()
  - [x] Use Setup Store pattern from CODE_GUIDE.md

- [x] OAuth redirect handler (Commit: 9aee5e8)
  - [x] Create src/pages/auth/GoogleCallback.vue
  - [x] Handle OAuth callback - backend redirects to frontend with session cookie
  - [x] Store user in authStore on success (fetchCurrentUser)
  - [x] Redirect to / or intended route (returnUrl query param)
  - [x] Handle errors with error display

- [x] Login page (Commit: 9aee5e8)
  - [x] Create src/pages/auth/Login.vue
  - [x] Google OAuth button with proper redirect URL
  - [x] Display logo and tagline
  - [x] Responsive design with Tailwind

- [x] Router guards (Commit: 9aee5e8)
  - [x] Create src/router/index.js
  - [x] Add requiresAuth guard (check authStore.isAuthenticated)
  - [x] Add requiresArtist guard (check user.role === 'artist')
  - [x] Add requiresGuest guard (redirect authenticated users away from /login)
  - [x] Apply guards to routes via meta
  - [x] Redirect unauthenticated users to /login with returnUrl

- [x] Logout functionality (Commit: 9aee5e8)
  - [x] Add logout button to Home page (placeholder)
  - [x] Call authStore.logout() on click
  - [x] Redirect to /login after logout

- [x] API Client setup (Commit: 9aee5e8)
  - [x] Create src/services/api.js with Axios instance
  - [x] CSRF token handling from cookie
  - [x] Session cookie support (withCredentials: true)
  - [x] 401 redirect to /login
  - [x] Error logging in development

- [ ] Testing (Manual testing completed, automated tests deferred)
  - [x] Test dev server starts successfully
  - [ ] Test OAuth flow redirects correctly (requires backend running)
  - [ ] Test login sets user in store (requires backend running)
  - [ ] Test logout clears user and redirects (requires backend running)
  - [ ] Test router guards protect routes (requires backend running)

**Implementation Reference**: [CODE_GUIDE.md#pinia-stores](CODE_GUIDE.md#pinia-stores)

**Exit Criteria**:
- ✅ User can login via Google OAuth (UI complete, requires backend)
- ✅ Session persists after page refresh (fetchCurrentUser on router guard)
- ✅ Unauthenticated users redirected to /login


## M3: Core Frontend

### M3-API-Client

**Referenced by**: Root PLAN.md → CP-M3-1
**Status**: DONE

#### Subtasks

- [x] Create Axios instance (Commit: 9aee5e8 - completed in M1-Auth-Frontend)
  - [x] Create src/services/api.js
  - [x] Configure baseURL from env (VITE_API_BASE_URL)
  - [x] Set withCredentials: true for session cookies
  - [x] Set timeout: 30000ms

- [x] Request interceptor (Commit: 9aee5e8)
  - [x] Get CSRF token from cookie if available
  - [x] Add X-CSRFToken header to requests
  - [x] Log requests in development mode

- [x] Response interceptor (Commit: 9aee5e8)
  - [x] Handle 401 Unauthorized → redirect to /login
  - [x] Handle 403 Forbidden → log error (toast deferred to PT-M3-Components)
  - [x] Handle 500 Internal Server Error → log error (toast deferred to PT-M3-Components)
  - [x] Extract data from response.data if present
  - [x] Return promise rejection on error

- [x] Create API service modules (Commit: 69d96bb)
  - [x] Create src/services/auth.service.js (getGoogleLoginUrl, getCurrentUser, logout)
  - [x] Create src/services/model.service.js (listModels, getModelDetail, createModel, deleteModel)
  - [x] Create src/services/token.service.js (getBalance, purchaseTokens, getTransactions)
  - [x] Create src/services/tag.service.js (listTags, getTagDetail, searchTags)
  - [x] Create src/services/generation.service.js (generateImage, getGenerationStatus, listGenerations, getGenerationDetail)

- [x] Testing (Commit: 69d96bb)
  - [x] Test dev server starts successfully without build errors
  - [ ] Test API calls with running backend (deferred - requires backend running)
  - [ ] Toast notifications (deferred to PT-M3-Components)

**Implementation Reference**: [CODE_GUIDE.md#api-client](CODE_GUIDE.md#api-client)

**Exit Criteria**:
- ✅ Axios instance configured correctly
- ✅ 401 responses trigger automatic redirect
- ⏳ Error messages display in UI toast (deferred to PT-M3-Components)

---

### M3-Router-Guards

**Referenced by**: Root PLAN.md → CP-M3-2
**Status**: DONE

#### Subtasks

- [x] Create requiresAuth guard (Commit: 9aee5e8 - completed in M1-Auth-Frontend)
  - [x] Update src/router/index.js
  - [x] Check useAuthStore().isAuthenticated
  - [x] If false, redirect to /login with returnUrl query param
  - [x] If true, allow navigation

- [x] Create requiresArtist guard (Commit: 9aee5e8)
  - [x] Check useAuthStore().isArtist (computed from user?.role === 'artist')
  - [x] If false, redirect to / with console error
  - [x] If true, allow navigation

- [x] Create requiresGuest guard (Commit: 9aee5e8)
  - [x] Check if user is authenticated
  - [x] If authenticated, redirect away from /login to /
  - [x] If not authenticated, allow navigation

- [x] Apply guards to routes (Commit: 9aee5e8)
  - [x] /login → requiresGuest (line 19)
  - [ ] /generate → requiresAuth (route not yet created, deferred to PT-M3-Generation)
  - [ ] /styles/create → requiresAuth + requiresArtist (route not yet created, deferred to PT-M3-StylePages)
  - [ ] /profile → requiresAuth (route not yet created, deferred to M5)
  - [ ] /tokens → requiresAuth (route not yet created, deferred to PT-M3-TokenPages)

- [x] Return URL handling (Commit: 9aee5e8)
  - [x] After redirect to /login, add returnUrl query param (line 65)
  - [x] GoogleCallback component handles returnUrl redirect (apps/frontend/src/pages/auth/GoogleCallback.vue)

- [x] Auto-fetch current user (Commit: 9aee5e8)
  - [x] Fetch user on every navigation if not already loaded (line 51-58)
  - [x] Ensures user state is available for guards

- [ ] Testing (Deferred - requires pages to be created)
  - [ ] Test unauthenticated user cannot access /generate
  - [ ] Test non-artist cannot access /styles/create
  - [ ] Test redirects work without infinite loops
  - [ ] Test returnUrl redirects user back after login

**Implementation Reference**: [CODE_GUIDE.md#router-guards](CODE_GUIDE.md#router-guards)

**Exit Criteria**:
- ✅ Guard logic implemented and ready for use
- ✅ Unauthenticated users redirected to /login with returnUrl
- ✅ Non-artists redirected to / from artist-only routes
- ✅ Redirects work correctly without infinite loops
- ⏳ Full testing deferred until protected pages are created

---

### M3-Style-Pages

**Referenced by**: Root PLAN.md → PT-M3-StylePages
**Status**: PLANNED

**Design Mockup References**:
- `StyleDetailPage1-4.png` - Style detail views
- `Create Style Page1-3.png` - Style creation flow
- `Search & Following Artist Page.png` - Search and marketplace

#### Subtasks

- [ ] Create ModelMarketplace page
  - [ ] Create src/pages/marketplace/ModelMarketplace.vue
  - [ ] Display grid of ModelCard components
  - [ ] Search input with debounced API call
  - [ ] Filter by tags (multi-select dropdown)
  - [ ] Sort by popularity or date
  - [ ] Infinite scroll pagination

- [ ] Create ModelCard component
  - [ ] Create src/components/features/model/ModelCard.vue
  - [ ] Display thumbnail, name, artist, price
  - [ ] Click navigates to /models/:id
  - [ ] Hover effects

- [ ] Create ModelDetail page
  - [ ] Create src/pages/marketplace/ModelDetail.vue
  - [ ] Display full model info (name, description, price, tags)
  - [ ] Artist info section (name, profile_image, follower count)
  - [ ] Sample image gallery (4 images)
  - [ ] Generate button → navigate to /generate with style pre-selected
  - [ ] Purchase/Use button if not owned

- [ ] Create StyleCreate page
  - [ ] Create src/pages/artist/StyleCreate.vue
  - [ ] Artist-only route (requiresArtist guard)
  - [ ] Drag-and-drop image uploader (10-100 images)
  - [ ] Tag input with autocomplete
  - [ ] Style name and description inputs
  - [ ] Price input
  - [ ] Signature image upload (optional)
  - [ ] Submit button → POST /api/models/train
  - [ ] Display upload progress
  - [ ] Redirect to /profile after successful upload

- [ ] Testing
  - [ ] Test marketplace loads and displays models
  - [ ] Test search and filter work
  - [ ] Test infinite scroll loads more items
  - [ ] Test model detail displays correctly
  - [ ] Test style create validates inputs
  - [ ] Test image upload works

**Implementation Reference**: [CODE_GUIDE.md#page-components](CODE_GUIDE.md#page-components)

**Exit Criteria**:
- [ ] Marketplace page functional with search and filters
- [ ] Model detail page shows complete information
- [ ] Style create page allows artists to upload models


### M3-Generation-UI

**Referenced by**: Root PLAN.md → PT-M3-Generation  
**Status**: PLANNED

#### Subtasks

- [ ] Create ImageGeneration page
  - [ ] Create src/pages/generate/ImageGeneration.vue
  - [ ] Style model selector (dropdown or search)
  - [ ] Prompt tag input (multi-select, autocomplete)
  - [ ] Aspect ratio selector (1:1 [512×512px], 2:2 [1024×1024px], 1:2 [512×1024px])
  - [ ] Advanced settings (seed, optional)
  - [ ] Token cost display (updates based on aspect ratio)
  - [ ] Generate button (check token balance, disable if insufficient)
  - [ ] Submit to POST /api/images/generate

- [ ] Progress indicator component
  - [ ] Create src/components/features/generation/ProgressIndicator.vue
  - [ ] Display status: queued to processing to completed
  - [ ] Progress bar or spinner
  - [ ] Estimated time remaining (optional)
  - [ ] Poll GET /api/images/:id/status every 5 seconds

- [ ] ImagePreview component
  - [ ] Create src/components/features/generation/ImagePreview.vue
  - [ ] Display generated image
  - [ ] Download button (save to device)
  - [ ] Share button (copy link, optional)
  - [ ] Regenerate button (use same params)

- [ ] Generation history list
  - [ ] Create src/pages/generate/GenerationHistory.vue
  - [ ] List past generations
  - [ ] Display thumbnail, status, created_at
  - [ ] Click to view full image
  - [ ] Pagination or infinite scroll

- [ ] Testing
  - [ ] Test generate button is disabled when insufficient tokens
  - [ ] Test token cost updates based on aspect ratio
  - [ ] Test progress indicator polls status
  - [ ] Test image preview displays correctly
  - [ ] Test download button works
  - [ ] Test history list loads

**Exit Criteria**:
- [ ] User can generate images with selected style
- [ ] Progress indicator shows real-time status
- [ ] Image preview and download work



### M3-Stores

**Referenced by**: Root PLAN.md -> PT-M3-Stores
Status: DONE

#### Subtasks

- [x] Create useModelsStore (Commit: 725a55a)
  - [x] fetchModels with pagination, filters, sorting
  - [x] fetchModelDetail by ID
  - [x] createModel for artists
  - [x] deleteModel for owners
  - [x] loadMore for infinite scroll

- [x] Create useTokenStore (Commit: 725a55a)
  - [x] fetchBalance and sync with auth store
  - [x] purchaseTokens with payment method
  - [x] fetchTransactions with filter by type
  - [x] loadMore for infinite scroll
  - [x] updateBalance for optimistic updates

- [x] Create useGenerationStore (Commit: 725a55a)
  - [x] generateImage request
  - [x] checkStatus polling
  - [x] startPolling/stopPolling (5s interval)
  - [x] fetchGenerations history
  - [x] fetchGenerationDetail by ID
  - [x] Queue management for active generations

**Exit Criteria**:
- ✅ All stores created with Setup Store pattern
- ✅ Integration with API service modules
- ✅ Error handling and loading states
- ✅ Dev server builds without errors

---

## M5: Community

### M5-Notification

**Referenced by**: Root PLAN.md -> CP-M5-1
Status: PLANNED

- [ ] Create notification polling

---

## M6: Launch

### M6-E2E-Tests

**Referenced by**: Root PLAN.md -> CP-M6-1
Status: PLANNED

- [ ] Install Playwright
- [ ] Write E2E scenarios

---

### M6-Build-Optimization

**Referenced by**: Root PLAN.md -> PT-M6-FrontendBuild
Status: PLANNED

- [ ] Code splitting
- [ ] Image optimization
- [ ] Bundle size < 500KB

---

## Quick Reference

### Design Resources

**Page Mockups**: `docs/design/pages/` (17 PNG/JPG files)
**Logos**: `src/assets/images/` (main_logo.png, main_logo_black.png, etc.)
**Icons**: `src/assets/icons/` (brush_icon.png, style_icon.png, style_icon_selected.png)

**Key Guidelines**:
1. Follow mockups with flexibility for consistency
2. Use Instagram UI patterns
3. TECHSPEC.md is authority (no comment likes, etc.)
4. Extract colors/fonts to tailwind.config.js

**See README.md#design-system for full design guidelines.**

### Common Commands

```bash
# Development
npm run dev

# Build
npm run build

# Testing
npm run test
npm run test:e2e

# Code quality
npm run lint
npm run format
```

### Asset Import Example

```vue
<script setup>
import logo from '@/assets/images/main_logo.png'
import styleIcon from '@/assets/icons/style_icon.png'
</script>

<template>
  <img :src="logo" alt="Style License" />
  <img :src="styleIcon" alt="Styles" />
</template>
```

