# Style License Development Plan

**Version**: 0.1.0  
**Last Updated**: 2025-10-27  
**Status**: M1 In Progress

---

## Overview
```
Total Progress: ██░░░░░░░░░░░░░░░░░░ 10%

M1 Foundation        ████░░░░░░░░░░░░░░░░ 20%
M2 Core Backend      ░░░░░░░░░░░░░░░░░░░░  0%
M3 Core Frontend     ░░░░░░░░░░░░░░░░░░░░  0%
M4 AI Integration    ░░░░░░░░░░░░░░░░░░░░  0%
M5 Community         ░░░░░░░░░░░░░░░░░░░░  0%
M6 Launch            ░░░░░░░░░░░░░░░░░░░░  0%
```

---

## Dependency Graph
```
M1 (Foundation)
├─→ M2 (Core Backend)
│   └─→ M4 (AI Integration)
│       └─→ M5 (Community)
│           └─→ M6 (Launch)
└─→ M3 (Core Frontend)
    └─→ M5 (Community)
        └─→ M6 (Launch)

M2 ⫽ M3  (병렬 가능)
M4: Training ⫽ Inference (병렬 가능)
```

---

## M1: Foundation

**ID**: M1
**Status**: IN_PROGRESS
**Dependencies**: []
**Blocking**: [M2, M3]
**Completion**: 20%

### Objectives
- [x] Docker infrastructure setup
- [ ] Database schema creation
- [ ] Authentication system implementation
- [ ] All services health check passing

### Critical Path (순차 실행 필수)
```
CP-M1-1 → CP-M1-2 → CP-M1-3
```

#### CP-M1-1: Infrastructure Setup
- **Status**: DONE
- **Type**: SEQUENTIAL
- **Owner**: DevOps
- **Tasks**:
  - [x] Docker Compose configuration
  - [x] PostgreSQL container setup
  - [x] RabbitMQ container setup
  - [x] Network and volume configuration
- **Exit Criteria**:
  - `docker-compose up` executes without errors
  - All containers report healthy status
  - RabbitMQ management UI accessible at localhost:15672

#### CP-M1-2: Database Schema
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [CP-M1-1]
- **Owner**: Backend
- **Tasks**:
  - [ ] User model with google_id, role, token_balance
  - [ ] StyleModel with training_status, signature fields
  - [ ] GeneratedImage with metadata
  - [ ] TokenTransaction with transaction_type
  - [ ] Tag, Follow, Notification, ImageLike, ImageComment models
  - [ ] Indexes on (user_id, created_at, training_status)
  - [ ] Foreign key constraints
- **Exit Criteria**:
  - `python manage.py migrate` succeeds
  - All models visible in Django admin
  - Can create/read/update/delete via admin panel
- **Reference**: [docs/database/README.md](docs/database/README.md)

#### CP-M1-3: Authentication Flow
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [CP-M1-2]
- **Owners**: [Backend, Frontend]
- **Tasks**:
  - [ ] Django-allauth configuration
  - [ ] Google OAuth provider setup
  - [ ] Session middleware configuration
  - [ ] GET /api/auth/google/login (OAuth redirect)
  - [ ] GET /api/auth/google/callback (OAuth callback handler)
  - [ ] POST /api/auth/logout endpoint
  - [ ] GET /api/auth/me endpoint
  - [ ] Frontend OAuth redirect handler
  - [ ] useAuthStore implementation
  - [ ] Router guards (requiresAuth, requiresArtist)
- **Exit Criteria**:
  - User can login via Google in browser
  - Session persists after page refresh
  - Unauthenticated users redirected to /login
  - Artist-only routes protected
- **Reference**:
  - [docs/API.md#authentication](docs/API.md#authentication)
  - [TECHSPEC.md#10-보안-설계](TECHSPEC.md#10-보안-설계)

### Parallel Tasks (병렬 실행 가능)
```
PT-M1-Backend ⫽ PT-M1-Frontend ⫽ PT-M1-Training ⫽ PT-M1-Inference
```

#### PT-M1-Backend: Backend Initialization
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M1-Frontend, PT-M1-Training, PT-M1-Inference]
- **Owner**: Backend
- **Reference**: [apps/backend/PLAN.md#m1-initialization](apps/backend/PLAN.md#m1-initialization)
- **Summary**:
  - [ ] Django project creation
  - [ ] PostgreSQL connection configuration
  - [ ] Django REST Framework setup
  - [ ] Health check endpoint: GET /api/health

#### PT-M1-Frontend: Frontend Initialization
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M1-Backend, PT-M1-Training, PT-M1-Inference]
- **Owner**: Frontend
- **Reference**: [apps/frontend/PLAN.md#m1-initialization](apps/frontend/PLAN.md#m1-initialization)
- **Summary**:
  - [ ] Vite + Vue 3 project setup
  - [ ] Tailwind CSS configuration
  - [ ] Pinia, Vue Router, Axios installation
  - [ ] i18n setup (en, ko)

#### PT-M1-Training: Training Server Initialization
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M1-Backend, PT-M1-Frontend, PT-M1-Inference]
- **Owner**: ML Engineer
- **Reference**: [apps/training-server/PLAN.md#m1-initialization](apps/training-server/PLAN.md#m1-initialization)
- **Summary**:
  - [ ] PyTorch, Diffusers installation
  - [ ] RabbitMQ connection test
  - [ ] CUDA availability check

#### PT-M1-Inference: Inference Server Initialization
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M1-Backend, PT-M1-Frontend, PT-M1-Training]
- **Owner**: ML Engineer
- **Reference**: [apps/inference-server/PLAN.md#m1-initialization](apps/inference-server/PLAN.md#m1-initialization)
- **Summary**:
  - [ ] Stable Diffusion installation
  - [ ] RabbitMQ connection test
  - [ ] Test inference with base model

### Exit Criteria
- [ ] All CP-M1 tasks completed
- [ ] All PT-M1 tasks completed
- [ ] `docker-compose up` starts all services successfully
- [ ] User can complete full login flow in browser
- [ ] Database contains all required tables

---

## M2: Core Backend

**ID**: M2  
**Status**: PLANNED  
**Dependencies**: [M1]  
**Blocking**: [M4]  
**Parallel With**: [M3]  
**Completion**: 0%

### Objectives
- [ ] Style model CRUD API operational
- [ ] Token system with transaction atomicity
- [ ] Tag system with filtering
- [ ] RabbitMQ integration functional

### Critical Path (순차 실행 필수)
```
CP-M2-1 → CP-M2-2 → CP-M2-3
```

#### CP-M2-1: API Foundation
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [M1]
- **Owner**: Backend
- **Tasks**:
  - [ ] DRF Serializer pattern establishment
  - [ ] ViewSet base class with pagination
  - [ ] Global exception handler
  - [ ] Response format standardization (success/error)
- **Exit Criteria**:
  - Consistent API response structure across all endpoints
  - Cursor-based pagination works with ?cursor=<timestamp>&limit=N
  - All errors return proper HTTP status codes

#### CP-M2-2: RabbitMQ Integration
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [CP-M2-1]
- **Owner**: Backend
- **Tasks**:
  - [ ] Message sender utility (send_training_task, send_generation_task)
  - [ ] Message format schema definition
  - [ ] Queue declaration (model_training, image_generation)
  - [ ] Connection pooling
  - [ ] Backend → Training Server message delivery test
- **Exit Criteria**:
  - Message appears in RabbitMQ queue after API call
  - Message contains all required fields
  - No connection leaks after 100 messages
- **Reference**: [docs/API.md#rabbitmq-integration](docs/API.md#rabbitmq-integration)

#### CP-M2-3: Token Transaction Atomicity
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [CP-M2-1]
- **Owner**: Backend
- **Tasks**:
  - [ ] TokenService.consume_tokens with SELECT FOR UPDATE
  - [ ] TokenService.add_tokens with transaction
  - [ ] TokenService.refund_tokens with transaction
  - [ ] Concurrent consumption test (100 simultaneous requests)
- **Exit Criteria**:
  - 100 concurrent consume_tokens calls succeed without race condition
  - Token balance is accurate after all transactions
  - All transactions logged in TokenTransaction table
- **Reference**: [apps/backend/PLAN.md#m2-token-service](apps/backend/PLAN.md#m2-token-service)

### Parallel Tasks (병렬 실행 가능)
```
PT-M2-StyleAPI ⫽ PT-M2-TokenAPI ⫽ PT-M2-TagAPI
```

#### PT-M2-StyleAPI: Style Model API
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M2-TokenAPI, PT-M2-TagAPI]
- **Dependencies**: [CP-M2-1, CP-M2-2]
- **Owner**: Backend
- **Reference**: [apps/backend/PLAN.md#m2-style-model-api](apps/backend/PLAN.md#m2-style-model-api)
- **Summary**:
  - [ ] POST /api/models/train (image upload, tag assignment, price)
  - [ ] GET /api/models (pagination, filter by tags/artist, sort by popular/recent)
  - [ ] GET /api/models/:id (detail with artist info, sample images)
  - [ ] DELETE /api/models/:id (owner-only permission check)
  - [ ] Validation: 10-100 images, JPG/PNG only, max 10MB each

#### PT-M2-TokenAPI: Token System API
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M2-StyleAPI, PT-M2-TagAPI]
- **Dependencies**: [CP-M2-1, CP-M2-3]
- **Owner**: Backend
- **Reference**: [apps/backend/PLAN.md#m2-token-api](apps/backend/PLAN.md#m2-token-api)
- **Summary**:
  - [ ] GET /api/tokens/balance
  - [ ] POST /api/tokens/purchase (payment gateway mock)
  - [ ] GET /api/tokens/transactions (filter by type, pagination)

#### PT-M2-TagAPI: Tag System
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M2-StyleAPI, PT-M2-TokenAPI]
- **Dependencies**: [CP-M2-1]
- **Owner**: Backend
- **Reference**: [apps/backend/PLAN.md#m2-tag-api](apps/backend/PLAN.md#m2-tag-api)
- **Summary**:
  - [ ] GET /api/tags (popular tags, usage_count > 0, limit 20)
  - [ ] GET /api/models?tags=watercolor,portrait (AND/OR logic)
  - [ ] Tag autocomplete endpoint

### Exit Criteria
- [ ] All CP-M2 tasks completed
- [ ] All PT-M2 tasks completed
- [ ] All endpoints return proper responses in Postman/Thunder Client
- [ ] RabbitMQ queue shows messages after POST /api/models/train
- [ ] Token concurrency test passes

---

## M3: Core Frontend

**ID**: M3  
**Status**: PLANNED  
**Dependencies**: [M1]  
**Blocking**: [M5]  
**Parallel With**: [M2]  
**Completion**: 0%

### Objectives
- [ ] All core pages rendering correctly
- [ ] API integration with proper error handling
- [ ] State management operational
- [ ] Route guards protecting authenticated routes

### Critical Path (순차 실행 필수)
```
CP-M3-1 → CP-M3-2
```

#### CP-M3-1: API Client Setup
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [M1]
- **Owner**: Frontend
- **Tasks**:
  - [ ] Axios instance configuration (baseURL, withCredentials)
  - [ ] Request interceptor (CSRF token from cookie)
  - [ ] Response interceptor (401 → redirect /login, 500 → toast error)
  - [ ] API client test with mock server
- **Exit Criteria**:
  - Authenticated requests include session cookie
  - 401 responses trigger automatic redirect
  - Error messages display in UI toast
- **Reference**: [apps/frontend/PLAN.md#m3-api-client](apps/frontend/PLAN.md#m3-api-client)

#### CP-M3-2: Router Guards
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [CP-M3-1]
- **Owner**: Frontend
- **Tasks**:
  - [ ] requiresAuth guard (check useAuthStore.isAuthenticated)
  - [ ] requiresArtist guard (check role === 'artist')
  - [ ] Guard application to protected routes
  - [ ] Redirect logic to /login or /
- **Exit Criteria**:
  - Unauthenticated user cannot access /generate
  - Non-artist cannot access /styles/create
  - Redirects work without infinite loops
- **Reference**: [apps/frontend/PLAN.md#m3-router-guards](apps/frontend/PLAN.md#m3-router-guards)

### Parallel Tasks (병렬 실행 가능)
```
PT-M3-Components ⫽ PT-M3-StylePages ⫽ PT-M3-Generation ⫽ PT-M3-Stores
```

#### PT-M3-Components: Common Components
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M3-StylePages, PT-M3-Generation, PT-M3-Stores]
- **Dependencies**: [M1]
- **Owner**: Frontend
- **Reference**: [apps/frontend/PLAN.md#m3-components](apps/frontend/PLAN.md#m3-components)
- **Summary**:
  - [ ] Button (variants: primary, secondary, outline, ghost)
  - [ ] Input (text, email, number, textarea)
  - [ ] Modal with backdrop click close
  - [ ] Card with hover effects
  - [ ] Header with auth status, token balance display
  - [ ] Footer
  - [ ] AppLayout (header + slot + footer)

#### PT-M3-StylePages: Style Related Pages
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M3-Components, PT-M3-Generation, PT-M3-Stores]
- **Dependencies**: [CP-M3-1]
- **Owner**: Frontend
- **Reference**: [apps/frontend/PLAN.md#m3-style-pages](apps/frontend/PLAN.md#m3-style-pages)
- **Summary**:
  - [ ] ModelMarketplace.vue (search, filter, infinite scroll)
  - [ ] ModelDetail.vue (artist info, sample gallery, generate button)
  - [ ] StyleCreate.vue (drag-and-drop images, tag input with autocomplete, signature upload)
  - [ ] ModelCard.vue component

#### PT-M3-Generation: Image Generation UI
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M3-Components, PT-M3-StylePages, PT-M3-Stores]
- **Dependencies**: [CP-M3-1]
- **Owner**: Frontend
- **Reference**: [apps/frontend/PLAN.md#m3-generation-ui](apps/frontend/PLAN.md#m3-generation-ui)
- **Summary**:
  - [ ] ImageGeneration.vue (style selector, prompt input, settings)
  - [ ] Progress indicator (queued → processing → completed)
  - [ ] ImagePreview with download button
  - [ ] Generation history list

#### PT-M3-Stores: Pinia State Management
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M3-Components, PT-M3-StylePages, PT-M3-Generation]
- **Dependencies**: [CP-M3-1]
- **Owner**: Frontend
- **Reference**: [apps/frontend/PLAN.md#m3-stores](apps/frontend/PLAN.md#m3-stores)
- **Summary**:
  - [ ] useModelsStore (fetchModels, fetchDetail, createModel)
  - [ ] useGenerationStore (generateImage, checkStatus, queue management)
  - [ ] useTokenStore (fetchBalance, purchaseTokens)

### Exit Criteria
- [ ] All CP-M3 tasks completed
- [ ] All PT-M3 tasks completed
- [ ] All pages accessible via router
- [ ] API calls display loading states
- [ ] Error states render properly

---

## M4: AI Integration

**ID**: M4  
**Status**: PLANNED  
**Dependencies**: [M2]  
**Blocking**: [M5]  
**Completion**: 0%

### Objectives
- [ ] LoRA training pipeline operational
- [ ] Image generation with signature insertion working
- [ ] End-to-end flow (upload → train → generate) functional
- [ ] Average training time < 30 minutes
- [ ] Average generation time < 10 seconds

### Critical Path (순차 실행 필수)
```
CP-M4-1 → CP-M4-2 → CP-M4-3
```

#### CP-M4-1: Training-Inference Connection
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [M2, PT-M4-Training, PT-M4-Inference]
- **Owners**: [ML Engineer, Backend]
- **Tasks**:
  - [ ] Shared storage path for LoRA weights
  - [ ] Training Server saves to /models/{model_id}/lora_weights.safetensors
  - [ ] Inference Server loads from same path
  - [ ] Backend stores model_path in StyleModel.model_path
  - [ ] Cross-server file access test
- **Exit Criteria**:
  - Training Server successfully saves LoRA weights
  - Inference Server can load and use those weights
  - Generated image shows style characteristics

#### CP-M4-2: Signature Insertion Validation
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [PT-M4-Inference]
- **Owner**: ML Engineer
- **Tasks**:
  - [ ] Position accuracy test (bottom-left, bottom-center, bottom-right)
  - [ ] Opacity range test (0.0 - 1.0)
  - [ ] Size scaling test (small, medium, large)
  - [ ] Metadata embedding verification
  - [ ] Visual inspection of 10 sample images
- **Exit Criteria**:
  - Signature appears in correct position within 5px tolerance
  - Opacity matches requested value
  - Image metadata contains artist_id and model_id
- **Reference**: [apps/inference-server/PLAN.md#m4-signature-validation](apps/inference-server/PLAN.md#m4-signature-validation)

#### CP-M4-3: E2E Flow Test
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [CP-M4-1, CP-M4-2, PT-M4-Backend]
- **Owners**: [All]
- **Tasks**:
  - [ ] Upload 10 images via POST /api/models/train
  - [ ] Monitor RabbitMQ queue
  - [ ] Wait for training completion
  - [ ] Generate image with trained model
  - [ ] Verify signature in output
  - [ ] Measure total time
- **Exit Criteria**:
  - Full flow completes without manual intervention
  - User receives notification on training completion
  - Generated image has correct signature
  - Total time: upload to final image < 35 minutes

### Parallel Tasks (병렬 실행 가능)
```
PT-M4-Training ⫽ PT-M4-Inference ⫽ PT-M4-Backend
```

#### PT-M4-Training: Training Pipeline
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M4-Inference, PT-M4-Backend]
- **Dependencies**: [M2]
- **Owner**: ML Engineer
- **Reference**: [apps/training-server/PLAN.md#m4-training-pipeline](apps/training-server/PLAN.md#m4-training-pipeline)
- **Summary**:
  - [ ] Image preprocessing (resize 512x512, format conversion)
  - [ ] LoRA fine-tuning (SD v1.5, lr=1e-4, epochs=100-500)
  - [ ] Checkpoint saving every 10 epochs
  - [ ] RabbitMQ Consumer for `model_training` queue
  - [ ] Status update via PATCH /api/models/:id/status
  - [ ] Retry logic (max 3 attempts) on failure

#### PT-M4-Inference: Inference Pipeline
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M4-Training, PT-M4-Backend]
- **Dependencies**: [M2]
- **Owner**: ML Engineer
- **Reference**: [apps/inference-server/PLAN.md#m4-inference-pipeline](apps/inference-server/PLAN.md#m4-inference-pipeline)
- **Summary**:
  - [ ] Stable Diffusion inference (50 steps, guidance_scale=7.5)
  - [ ] LoRA weight loading from file path
  - [ ] Signature insertion with PIL (position, opacity, size)
  - [ ] Batch processing (10 concurrent generations)
  - [ ] RabbitMQ Consumer for `image_generation` queue
  - [ ] Status update via PATCH /api/images/:id/status

#### PT-M4-Backend: Backend AI Integration
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M4-Training, PT-M4-Inference]
- **Dependencies**: [M2]
- **Owner**: Backend
- **Reference**: [apps/backend/PLAN.md#m4-ai-integration](apps/backend/PLAN.md#m4-ai-integration)
- **Summary**:
  - [ ] PATCH /api/models/:id/status webhook endpoint
  - [ ] POST /api/notifications for training complete/failed
  - [ ] Token refund trigger on generation failure
  - [ ] POST /api/images/generate endpoint
  - [ ] GET /api/images/:id/status polling endpoint

### Exit Criteria
- [ ] All CP-M4 tasks completed
- [ ] All PT-M4 tasks completed
- [ ] Can train model with 10 images in < 30 minutes
- [ ] Can generate image with signature in < 10 seconds
- [ ] No manual intervention required for E2E flow

---

## M5: Community

**ID**: M5  
**Status**: PLANNED  
**Dependencies**: [M2, M3, M4]  
**Blocking**: [M6]  
**Completion**: 0%

### Objectives
- [ ] Public feed operational
- [ ] Like, comment, follow features working
- [ ] Real-time notification system functional
- [ ] Feed loads < 1 second for 100 items

### Critical Path (순차 실행 필수)
```
CP-M5-1 → CP-M5-2
```

#### CP-M5-1: Notification System
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [M2, M3]
- **Owners**: [Backend, Frontend]
- **Tasks**:
  - [ ] Notification trigger on like creation
  - [ ] Notification trigger on comment creation
  - [ ] Notification trigger on follow
  - [ ] Notification trigger on training complete/failed
  - [ ] GET /api/notifications endpoint with pagination
  - [ ] PATCH /api/notifications/:id/read
  - [ ] Frontend polling every 5 seconds when user active
  - [ ] Badge count on header notification icon
- **Exit Criteria**:
  - Like action creates notification for image owner
  - Notification list updates within 5 seconds
  - Badge count shows unread notifications
- **Reference**: 
  - [apps/backend/PLAN.md#m5-notification](apps/backend/PLAN.md#m5-notification)
  - [apps/frontend/PLAN.md#m5-notification](apps/frontend/PLAN.md#m5-notification)

#### CP-M5-2: Feed Algorithm
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [CP-M5-1]
- **Owner**: Backend
- **Tasks**:
  - [ ] Feed query optimization (select_related, prefetch_related)
  - [ ] Sort by created_at DESC
  - [ ] Filter by visibility (public only)
  - [ ] Optional: prioritize followed artists
  - [ ] Pagination with cursor or offset
- **Exit Criteria**:
  - Feed API response time < 200ms for 20 items
  - No N+1 query issues
  - Infinite scroll works without duplicate items

### Parallel Tasks (병렬 실행 가능)
```
PT-M5-CommunityBackend ⫽ PT-M5-CommunityFrontend
```

#### PT-M5-CommunityBackend: Community API
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M5-CommunityFrontend]
- **Dependencies**: [M2]
- **Owner**: Backend
- **Reference**: [apps/backend/PLAN.md#m5-community-api](apps/backend/PLAN.md#m5-community-api)
- **Summary**:
  - [ ] GET /api/community/feed (pagination, filter public images)
  - [ ] GET /api/images/:id (detail with like_count, comment_count)
  - [ ] POST /api/images/:id/like (toggle, prevent duplicate via unique constraint)
  - [ ] GET /api/images/:id/comments (pagination)
  - [ ] POST /api/images/:id/comments (content validation)
  - [ ] DELETE /api/comments/:id (owner or admin only)
  - [ ] POST /api/artists/:id/follow (toggle)
  - [ ] GET /api/users/following

#### PT-M5-CommunityFrontend: Community UI
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M5-CommunityBackend]
- **Dependencies**: [M3]
- **Owner**: Frontend
- **Reference**: [apps/frontend/PLAN.md#m5-community-ui](apps/frontend/PLAN.md#m5-community-ui)
- **Summary**:
  - [ ] Community.vue page (masonry or grid layout)
  - [ ] FeedDetail.vue (full image, artist info, comments)
  - [ ] FeedItem.vue component with like button animation
  - [ ] CommentList.vue with nested replies (optional)
  - [ ] Infinite scroll on Community page
  - [ ] Like button optimistic update
  - [ ] Notification dropdown in Header

### Exit Criteria
- [ ] All CP-M5 tasks completed
- [ ] All PT-M5 tasks completed
- [ ] Feed loads and scrolls smoothly
- [ ] Like/comment actions reflect immediately
- [ ] Notifications appear within 5 seconds

---

## M6: Launch

**ID**: M6  
**Status**: PLANNED  
**Dependencies**: [M5]  
**Blocking**: []  
**Completion**: 0%

### Objectives
- [ ] All E2E tests passing
- [ ] Production deployment successful
- [ ] Monitoring and logging operational
- [ ] Zero critical bugs

### Critical Path (순차 실행 필수)
```
CP-M6-1 → CP-M6-2 → CP-M6-3 → CP-M6-4
```

#### CP-M6-1: E2E Testing
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [M5]
- **Owners**: [All]
- **Tasks**:
  - [ ] Playwright scenario: signup → login → browse models
  - [ ] Scenario: create model → wait for training → generate image
  - [ ] Scenario: purchase tokens → generate image → verify deduction
  - [ ] Scenario: like image → comment → receive notification
  - [ ] Run all scenarios in CI pipeline
- **Exit Criteria**:
  - All scenarios pass without manual intervention
  - Test suite completes in < 10 minutes
  - No flaky tests (99% pass rate over 10 runs)
- **Reference**: [apps/frontend/PLAN.md#m6-e2e-tests](apps/frontend/PLAN.md#m6-e2e-tests)

#### CP-M6-2: Performance Testing
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [CP-M6-1]
- **Owners**: [Backend, DevOps]
- **Tasks**:
  - [ ] Load test with 100 concurrent users (k6 or Locust)
  - [ ] Measure API response times (p50, p95, p99)
  - [ ] Measure image generation queue throughput
  - [ ] Identify bottlenecks (DB queries, GPU memory)
  - [ ] Optimize slow queries (add indexes, caching)
- **Exit Criteria**:
  - p95 API response time < 500ms
  - System handles 100 concurrent users without errors
  - GPU queue processes 10 images/minute
- **Reference**: [apps/backend/PLAN.md#m6-performance](apps/backend/PLAN.md#m6-performance)

#### CP-M6-3: Production Deployment
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [CP-M6-2]
- **Owners**: [DevOps, Backend, Frontend]
- **Tasks**:
  - [ ] Environment variables configuration (secrets management)
  - [ ] HTTPS setup with Let's Encrypt or ACM
  - [ ] Domain DNS configuration
  - [ ] Backend deployment (Gunicorn + Nginx or AWS ECS)
  - [ ] Frontend deployment (Vercel, Netlify, or S3 + CloudFront)
  - [ ] Database migration on production
  - [ ] Smoke test on production URL
- **Exit Criteria**:
  - Application accessible via HTTPS at production domain
  - No SSL certificate warnings
  - Database migrations applied successfully
  - Basic user flow works (login, browse, generate)
- **Reference**: [DOCKER.md](DOCKER.md)

#### CP-M6-4: Monitoring Setup
- **Status**: PLANNED
- **Type**: SEQUENTIAL
- **Dependencies**: [CP-M6-3]
- **Owners**: [DevOps, Backend]
- **Tasks**:
  - [ ] Sentry error tracking for Backend and Frontend
  - [ ] Server resource monitoring (CPU, RAM, Disk)
  - [ ] GPU utilization tracking (NVIDIA-SMI or CloudWatch)
  - [ ] RabbitMQ queue length monitoring
  - [ ] Uptime monitoring (UptimeRobot or StatusCake)
  - [ ] Alert rules for critical errors
- **Exit Criteria**:
  - Errors appear in Sentry dashboard
  - Server metrics visible in monitoring tool
  - Receive alert when error rate > 10/minute
- **Reference**: [DOCKER.md](DOCKER.md)

### Parallel Tasks (병렬 실행 가능)
```
PT-M6-BackendDeploy ⫽ PT-M6-FrontendBuild ⫽ PT-M6-CICD
```

#### PT-M6-BackendDeploy: Backend Production Config
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M6-FrontendBuild, PT-M6-CICD]
- **Dependencies**: [M5]
- **Owner**: Backend
- **Reference**: [apps/backend/PLAN.md#m6-production-config](apps/backend/PLAN.md#m6-production-config)
- **Summary**:
  - [ ] Production settings.py (DEBUG=False, ALLOWED_HOSTS)
  - [ ] Static files collection (WhiteNoise or S3)
  - [ ] Gunicorn configuration (workers, timeout)
  - [ ] Nginx reverse proxy config
  - [ ] Database connection pooling

#### PT-M6-FrontendBuild: Frontend Optimization
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M6-BackendDeploy, PT-M6-CICD]
- **Dependencies**: [M5]
- **Owner**: Frontend
- **Reference**: [apps/frontend/PLAN.md#m6-build-optimization](apps/frontend/PLAN.md#m6-build-optimization)
- **Summary**:
  - [ ] Code splitting (route-based lazy loading)
  - [ ] Image optimization (WebP format, responsive sizes)
  - [ ] Tree shaking verification
  - [ ] Bundle size analysis (<500KB initial)
  - [ ] Lighthouse score 90+ (Performance, Accessibility, Best Practices, SEO)

#### PT-M6-CICD: CI/CD Pipeline
- **Status**: PLANNED
- **Type**: PARALLEL
- **Can Run With**: [PT-M6-BackendDeploy, PT-M6-FrontendBuild]
- **Dependencies**: [M5]
- **Owner**: DevOps
- **Reference**: [DOCKER.md](DOCKER.md), [TECHSPEC.md Section 14](TECHSPEC.md#14-배포-및-cicd)
- **Summary**:
  - [ ] GitHub Actions workflow for Backend (test → build → deploy)
  - [ ] GitHub Actions workflow for Frontend (test → build → deploy)
  - [ ] Auto-deploy on push to main branch
  - [ ] Rollback mechanism

### Exit Criteria
- [ ] All CP-M6 tasks completed
- [ ] All PT-M6 tasks completed
- [ ] Production URL is live and functional
- [ ] All monitoring alerts configured
- [ ] Zero critical bugs reported

---

## Status Codes

- **DONE**: Completed
- **IN_PROGRESS**: Currently being worked on
- **PLANNED**: Scheduled but not started
- **BLOCKED**: Cannot proceed due to dependency

## Task Types

- **SEQUENTIAL**: Must be completed before next task
- **PARALLEL**: Can be worked on simultaneously with other PARALLEL tasks

---

## Quick Reference

### How to Use This Plan

1. **Check Current Milestone**: Look at the milestone with `IN_PROGRESS` status
2. **Identify Your Role**: Find tasks assigned to your role (Backend, Frontend, ML Engineer, DevOps)
3. **Check Dependencies**: Ensure all dependencies are `DONE` before starting
4. **Follow Critical Path First**: Complete `CP-*` tasks before `PT-*` tasks
5. **Work in Parallel**: `PT-*` tasks can be done simultaneously with others
6. **Update Status**: Mark tasks as complete in both root PLAN.md and app-specific PLAN.md
7. **Check Exit Criteria**: Verify all exit criteria before marking milestone complete

### Finding Detailed Instructions

- Root PLAN.md: High-level milestones and dependencies
- App PLAN.md: Detailed subtasks, code patterns, test cases
- docs/: API specs, database schema, security policies
- claude.md: AI assistant guidance for implementation

---