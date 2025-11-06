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
**Status**: PLANNED

#### Subtasks

- [x] Vite + Vue 3 project setup
  - [x] npm create vite@latest . -- --template vue
  - [x] Configure vite.config.js with alias (@/ for src/)
  - [x] Set up development server on port 3000

- [x] Tailwind CSS configuration
  - [x] Install tailwindcss, postcss, autoprefixer
  - [x] Create tailwind.config.js
  - [x] Add Tailwind directives to src/assets/main.css
  - [x] Test Tailwind classes render correctly

- [x] Install core dependencies
  - [x] Install Pinia for state management
  - [x] Install Vue Router for routing
  - [x] Install Axios for HTTP requests
  - [x] Install vue-i18n for internationalization

- [x] i18n setup (en, ko)
  - [x] Create src/i18n/index.js
  - [x] Create src/locales/en.json and ko.json
  - [x] Configure default locale: en
  - [x] Add language switcher to header (optional)

- [x] Directory structure setup
  - [x] Create src/components/ (shared, features/)
  - [x] Create src/pages/
  - [x] Create src/stores/
  - [x] Create src/composables/
  - [x] Create src/services/
  - [x] Create src/assets/

- [x] Docker configuration
  - [x] Verify Dockerfile multi-stage build
  - [x] Test container starts with docker-compose up frontend

**Exit Criteria**:
- ✅ npm run dev starts dev server on localhost:3000
- ✅ Tailwind CSS classes work
- ✅ All dependencies installed without errors

---

### M1-Auth-Frontend

**Referenced by**: Root PLAN.md → CP-M1-3  
**Status**: IN_PROGRESS

#### Subtasks

- [ ] Create useAuthStore
  - [ ] Create src/stores/auth.js
  - [ ] State: user (null or user object), isAuthenticated (computed)
  - [ ] Actions: login(credentials), logout(), fetchMe()
  - [ ] Use Setup Store pattern from CODE_GUIDE.md

- [ ] OAuth redirect handler
  - [ ] Create src/pages/auth/GoogleCallback.vue
  - [ ] Parse OAuth code from URL query params
  - [ ] Handle OAuth callback - backend redirects to frontend with session cookie
  - [ ] Store user in authStore on success
  - [ ] Redirect to / or intended route
  - [ ] Handle errors with toast notification

- [ ] Login page
  - [ ] Create src/pages/auth/Login.vue
  - [ ] Google OAuth button with proper redirect URL
  - [ ] Display logo and tagline
  - [ ] Responsive design with Tailwind

- [ ] Router guards
  - [ ] Update src/router/index.js
  - [ ] Add requiresAuth guard (check authStore.isAuthenticated)
  - [ ] Add requiresArtist guard (check user.role === 'artist')
  - [ ] Apply guards to protected routes
  - [ ] Redirect unauthenticated users to /login

- [ ] Logout functionality
  - [ ] Add logout button to Header component
  - [ ] Call authStore.logout() on click
  - [ ] Redirect to /login after logout

- [ ] Testing
  - [ ] Test OAuth flow redirects correctly
  - [ ] Test login sets user in store
  - [ ] Test logout clears user and redirects
  - [ ] Test router guards protect routes

**Implementation Reference**: [CODE_GUIDE.md#pinia-stores](CODE_GUIDE.md#pinia-stores)

**Exit Criteria**:
- [ ] User can login via Google OAuth
- [ ] Session persists after page refresh
- [ ] Unauthenticated users redirected to /login


## M3: Core Frontend

### M3-API-Client

**Referenced by**: Root PLAN.md → CP-M3-1  
**Status**: PLANNED

#### Subtasks

- [ ] Create Axios instance
  - [ ] Create src/services/api.js
  - [ ] Configure baseURL from env (VITE_API_BASE_URL)
  - [ ] Set withCredentials: true for session cookies
  - [ ] Set timeout: 30000ms

- [ ] Request interceptor
  - [ ] Get CSRF token from cookie if available
  - [ ] Add X-CSRFToken header to requests
  - [ ] Log requests in development mode

- [ ] Response interceptor
  - [ ] Handle 401 Unauthorized → redirect to /login
  - [ ] Handle 403 Forbidden → show permission denied toast
  - [ ] Handle 500 Internal Server Error → show error toast
  - [ ] Extract data from response.data.data if present
  - [ ] Return promise rejection on error

- [ ] Create API service modules
  - [ ] Create src/services/auth.service.js (login, logout, me)
  - [ ] Create src/services/model.service.js (list, detail, create, delete)
  - [ ] Create src/services/token.service.js (balance, purchase, transactions)
  - [ ] Create src/services/generation.service.js (generate, status)

- [ ] Testing
  - [ ] Test authenticated requests include session cookie
  - [ ] Test 401 response triggers redirect
  - [ ] Test error responses show toast notifications
  - [ ] Test API service methods return correct data

**Implementation Reference**: [CODE_GUIDE.md#api-client](CODE_GUIDE.md#api-client)

**Exit Criteria**:
- [ ] Axios instance configured correctly
- [ ] 401 responses trigger automatic redirect
- [ ] Error messages display in UI toast

---

### M3-Router-Guards

**Referenced by**: Root PLAN.md → CP-M3-2  
**Status**: PLANNED

#### Subtasks

- [ ] Create requiresAuth guard
  - [ ] Update src/router/index.js
  - [ ] Check useAuthStore().isAuthenticated
  - [ ] If false, redirect to /login with returnUrl query param
  - [ ] If true, allow navigation

- [ ] Create requiresArtist guard
  - [ ] Check useAuthStore().user?.role === 'artist'
  - [ ] If false, redirect to / with error toast
  - [ ] If true, allow navigation

- [ ] Apply guards to routes
  - [ ] /generate → requiresAuth
  - [ ] /styles/create → requiresAuth + requiresArtist
  - [ ] /profile → requiresAuth
  - [ ] /tokens → requiresAuth

- [ ] Return URL handling
  - [ ] After login, check for returnUrl query param
  - [ ] Redirect to returnUrl if present
  - [ ] Otherwise redirect to /

- [ ] Testing
  - [ ] Test unauthenticated user cannot access /generate
  - [ ] Test non-artist cannot access /styles/create
  - [ ] Test redirects work without infinite loops
  - [ ] Test returnUrl redirects user back after login

**Implementation Reference**: [CODE_GUIDE.md#router-guards](CODE_GUIDE.md#router-guards)

**Exit Criteria**:
- [ ] Unauthenticated users cannot access protected routes
- [ ] Non-artists cannot access artist-only routes
- [ ] Redirects work correctly

---

### M3-Components

**Referenced by**: Root PLAN.md → PT-M3-Components  
**Status**: PLANNED

#### Subtasks

- [ ] Create Button component
  - [ ] Create src/components/shared/Button.vue
  - [ ] Props: variant (primary, secondary, outline, ghost), size (sm, md, lg), loading
  - [ ] Emit click event
  - [ ] Tailwind classes for each variant
  - [ ] Loading spinner when loading=true

- [ ] Create Input component
  - [ ] Create src/components/shared/Input.vue
  - [ ] Props: type (text, email, number, textarea), placeholder, modelValue
  - [ ] Emit update:modelValue for v-model
  - [ ] Error state styling
  - [ ] Label and helper text slots

- [ ] Create Modal component
  - [ ] Create src/components/shared/Modal.vue
  - [ ] Props: isOpen, title
  - [ ] Slots: default (content), actions (footer buttons)
  - [ ] Emit close on backdrop click or X button
  - [ ] Teleport to body for proper z-index

- [ ] Create Card component
  - [ ] Create src/components/shared/Card.vue
  - [ ] Props: clickable (boolean)
  - [ ] Hover effects if clickable
  - [ ] Slots: default (content)

- [ ] Create Header component
  - [ ] Create src/components/layout/Header.vue
  - [ ] Logo and navigation links
  - [ ] Display token balance if authenticated
  - [ ] User dropdown menu (profile, logout)
  - [ ] Mobile responsive hamburger menu

- [ ] Create Footer component
  - [ ] Create src/components/layout/Footer.vue
  - [ ] Links to docs, about, terms
  - [ ] Copyright notice

- [ ] Create AppLayout component
  - [ ] Create src/components/layout/AppLayout.vue
  - [ ] Render Header + slot + Footer
  - [ ] Apply to all pages via router

- [ ] Testing
  - [ ] Test Button variants render correctly
  - [ ] Test Input v-model works
  - [ ] Test Modal opens and closes
  - [ ] Test Header displays user info when authenticated

**Implementation Reference**:
- [CODE_GUIDE.md#components](CODE_GUIDE.md#components)
- **Design mockups**: All page mockups in `docs/design/pages/` show component usage

**Exit Criteria**:
- [ ] All base components created and functional
- [ ] Components follow design system (colors, spacing, fonts)
- [ ] Mobile responsive
- [ ] Assets (logos, icons) imported from `src/assets/`

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
  - [ ] Aspect ratio selector (1:1, 16:9, 9:16, 4:3, 3:4)
  - [ ] Advanced settings (seed, optional)
  - [ ] Token cost display (updates based on aspect ratio)
  - [ ] Generate button (check token balance, disable if insufficient)
  - [ ] Submit to POST /api/images/generate

- [ ] Progress indicator component
  - [ ] Create src/components/features/generation/ProgressIndicator.vue
  - [ ] Display status: queued to processing to completed
  - [ ] Progress bar or spinner
  - [ ] Estimated time remaining (optional)
  - [ ] Poll GET /api/images/:id/status every 2 seconds

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
Status: PLANNED

- [ ] Create useModelsStore, useGenerationStore, useTokenStore

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

