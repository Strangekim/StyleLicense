# Backend Development Plan

**App**: Backend (Django REST Framework)  
**Last Updated**: 2025-11-05  
**Status**: M1 In Progress

---

## Overview

This document contains detailed subtasks for backend development. For high-level milestones and dependencies, see [root PLAN.md](../../PLAN.md).

**Reference Documents**:
- [Backend README.md](README.md) - Architecture and directory structure
- [Backend CODE_GUIDE.md](CODE_GUIDE.md) - Code patterns and conventions
- [API Documentation](../../docs/API.md) - API specifications
- [Database Schema](../../docs/database/README.md) - Data models

---

## M1: Foundation

### M1-Initialization

**Referenced by**: Root PLAN.md → PT-M1-Backend
**Status**: DONE

#### Subtasks

- [x] Create Django project structure (Commit: 91ecbfc)
  - [x] django-admin startproject config .
  - [x] Create app/ directory for main application
  - [x] Configure config/settings.py with app registration

- [x] Install and configure dependencies (Commit: 91ecbfc)
  - [x] Create requirements.txt with Django, DRF, psycopg2, gunicorn
  - [x] Install django-cors-headers
  - [x] Install pika (RabbitMQ client)
  - [x] Install pillow for image handling

- [x] PostgreSQL connection configuration (Commit: 91ecbfc, 0bb8e02)
  - [x] Configure DATABASES in settings.py with DATABASE_URL
  - [x] Install dj-database-url for connection parsing
  - [x] Test connection with python manage.py dbshell (Commit: 0bb8e02)

- [x] Django REST Framework setup (Commit: 91ecbfc)
  - [x] Add rest_framework to INSTALLED_APPS
  - [x] Configure REST_FRAMEWORK settings (pagination, authentication)
  - [x] Set default renderer and parser classes

- [x] Health check endpoint (Commit: 0bb8e02)
  - [x] Create app/views/health.py with HealthCheckView
  - [x] Add route: GET /api/health returns {"status": "ok", "database": "connected"}
  - [x] Test database connectivity in health check

- [x] Docker configuration (Commit: 0bb8e02)
  - [x] Verify Dockerfile builds successfully
  - [x] Test container starts with docker-compose up backend

- [x] Database models creation (Commit: 91ecbfc)
  - [x] User and Artist models
  - [x] Style and Artwork models
  - [x] Generation model
  - [x] Transaction and Purchase models
  - [x] Tag models (Tag, StyleTag, ArtworkTag, GenerationTag)
  - [x] Community models (Follow, Like, Comment)
  - [x] Notification model
  - [x] All models registered in Django admin
  - [x] Initial migration created (0001_initial.py)

**Exit Criteria**:
- ✅ python manage.py runserver starts without errors
- ✅ GET /api/health returns 200 OK
- ✅ Database connection test passes (verified through Docker)

---

### M1-Auth-Backend

**Referenced by**: Root PLAN.md → CP-M1-3
**Status**: DONE

#### Subtasks

- [x] Install and configure django-allauth (Commit: 0d1927a)
  - [x] Add to requirements.txt: django-allauth[socialaccount]
  - [x] Add to INSTALLED_APPS: allauth, allauth.account, allauth.socialaccount, allauth.socialaccount.providers.google
  - [ ] Run migrations: python manage.py migrate (requires PostgreSQL running)

- [x] Google OAuth provider setup (Commit: 0d1927a)
  - [x] Configure SOCIALACCOUNT_PROVIDERS in settings.py
  - [x] Set GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET from env
  - [x] Configure callback URL: /api/auth/google/callback

- [x] Session middleware configuration (Commit: 0d1927a)
  - [x] Ensure django.contrib.sessions.middleware.SessionMiddleware in MIDDLEWARE
  - [x] Configure SESSION_COOKIE_HTTPONLY = True
  - [x] Configure SESSION_COOKIE_SAMESITE = Lax
  - [x] Set SESSION_COOKIE_AGE = 1209600 (2 weeks)

- [x] Authentication endpoints (Commit: 0d1927a)
  - [x] Create app/views/auth.py
  - [x] GET /api/auth/google/login - OAuth redirect to Google
  - [x] GET /api/auth/google/callback - OAuth callback handler
    - [x] Validate Google OAuth code
    - [x] Get or create User with provider and provider_user_id
    - [x] Grant welcome tokens for new users
      - [x] Check if user is newly created (first login)
      - [x] Call TokenService.add_tokens(user_id, 100, 'welcome_bonus')
      - [x] Create TokenTransaction record with type='earn'
    - [x] Create session
    - [x] Return user data
  - [x] POST /api/auth/logout
    - [x] Clear session
    - [x] Return success response
  - [x] GET /api/auth/me
    - [x] Return current user if authenticated
    - [x] Return 401 if not authenticated

- [x] User model customization (Commit: 91ecbfc - completed in M1-Database)
  - [x] Extend AbstractUser in app/models/user.py
  - [x] Add fields: provider, provider_user_id, role, token_balance, profile_image
  - [x] Create migration

- [x] URL routing (Commit: 0d1927a)
  - [x] Add auth routes to app/urls.py
  - [x] Include allauth URLs

- [x] Testing (Commit: eb925d5)
  - [x] Write test: successful Google login creates user and session
  - [x] Write test: logout clears session
  - [x] Write test: /api/auth/me returns user data when authenticated
  - [x] Write test: /api/auth/me returns 401 when unauthenticated
  - [x] Write test: TokenService.add_tokens increases balance
  - [x] Write test: TokenService.consume_tokens decreases balance
  - [x] Write test: TokenService.consume_tokens with insufficient balance raises error
  - [x] Write test: Welcome bonus only granted once

**Implementation Reference**: [CODE_GUIDE.md#authentication](CODE_GUIDE.md#authentication)

**Exit Criteria**:
- [x] User can authenticate via Google OAuth (implementation complete)
- [x] Session persists across requests (implementation complete)
- [x] All auth tests pass (9/9 tests passing)


## M2: Core Backend

### M2-API-Foundation

**Referenced by**: Root PLAN.md → CP-M2-1
**Status**: DONE

#### Subtasks

- [x] Create base serializer pattern (Commit: 859583f)
  - [x] Create app/serializers/base.py
  - [x] Define BaseSerializer with dynamic field filtering
  - [x] Document in CODE_GUIDE.md if needed

- [x] Create base ViewSet with pagination (Commit: 859583f)
  - [x] Create app/views/base.py
  - [x] Define BaseViewSet extending ModelViewSet
  - [x] Configure CustomCursorPagination (page_size=20, ordering='-created_at')
  - [x] Override CRUD methods for consistent response format
  - [x] Add get_queryset optimization helpers (select_related, prefetch_related)

- [x] Global exception handler (Commit: 859583f)
  - [x] Create app/exceptions.py with custom exception classes
  - [x] Define custom_exception_handler in app/utils/exception_handler.py
  - [x] Handle ValidationError, PermissionDenied, NotFound, Http404
  - [x] Format errors consistently: {"success": false, "error": {"code": "ERROR_CODE", "message": "..."}}
  - [x] Configure in settings.py: REST_FRAMEWORK['EXCEPTION_HANDLER']

- [x] Response format standardization (Commit: 859583f)
  - [x] Success responses: {"success": true, "data": {...}}
  - [x] Error responses: {"success": false, "error": {"code": "CODE", "message": "..."}}
  - [x] Paginated responses use DRF's CursorPagination format

- [x] Testing (Commit: 859583f)
  - [x] Test BaseSerializer dynamic field filtering
  - [x] Test custom exception formatting (InsufficientTokensError, ValidationError)
  - [x] Test success response format
  - [x] Test cursor pagination configuration (6/6 tests passing)

**Exit Criteria**:
- ✅ All endpoints use consistent response structure
- ✅ Pagination works correctly (CustomCursorPagination configured)
- ✅ Error handling returns proper HTTP status codes

---

### M2-RabbitMQ-Integration

**Referenced by**: Root PLAN.md → CP-M2-2
**Status**: DONE

#### Subtasks

- [x] Create message sender utility (Commit: 6c4bfec)
  - [x] Create app/services/rabbitmq_service.py
  - [x] Implement send_training_task(style_id, image_paths, webhook_url)
  - [x] Implement send_generation_task(generation_id, style_id, prompt, webhook_url)
  - [x] Use pika library for connection

- [x] Define message format schema (Commit: 6c4bfec)
  - [x] Training message: {"task_id": uuid, "type": "model_training", "data": {"style_id": int, "image_paths": [str], "num_epochs": int}, "webhook_url": str}
  - [x] Generation message: {"task_id": uuid, "type": "image_generation", "data": {"generation_id": int, "style_id": int, "lora_path": str, "prompt": str, "aspect_ratio": str, "seed": int}, "webhook_url": str}
  - [ ] Document in docs/API.md (deferred)

- [x] Queue declaration (Commit: 6c4bfec)
  - [x] Declare model_training queue (durable=True)
  - [x] Declare image_generation queue (durable=True)
  - [x] Queue declared on publish (idempotent)

- [x] Connection pooling (Commit: 6c4bfec)
  - [x] Connection reuse with context manager
  - [x] Implement connection retry logic (max 3 attempts)
  - [x] Close connections gracefully on application shutdown

- [x] Testing (Commit: 6c4bfec)
  - [x] Test message delivery to RabbitMQ (mocked, 8/8 passing)
  - [x] Verify message format
  - [x] Test connection retry logic
  - [x] Test no connection leaks
  - [x] Test singleton pattern
  - [x] Test webhook URL generation

**Implementation Reference**: [CODE_GUIDE.md#rabbitmq-integration](CODE_GUIDE.md#rabbitmq-integration)

**Exit Criteria**:
- ✅ Messages appear in RabbitMQ queue after API call (implementation complete)
- ✅ Message format matches schema
- ✅ No connection leaks (context manager + singleton)

---

### M2-Token-Service

**Referenced by**: Root PLAN.md → CP-M2-3
**Status**: DONE

#### Subtasks

- [x] Create TokenService class (Previously implemented)
  - [x] Create app/services/token_service.py
  - [x] Define TokenService with static methods

- [x] Implement consume_tokens with SELECT FOR UPDATE (Previously implemented)
  - [x] Method signature: consume_tokens(user_id: int, amount: int, reason: str) -> bool
  - [x] Use @transaction.atomic decorator
  - [x] Query: User.objects.select_for_update().get(id=user_id)
  - [x] Check if user.token_balance >= amount
  - [x] Deduct tokens: user.token_balance -= amount
  - [x] Create TokenTransaction record (type=consume, amount, reason)
  - [x] Return True on success, raise exception on insufficient balance

- [x] Implement add_tokens with transaction (Previously implemented)
  - [x] Method signature: add_tokens(user_id: int, amount: int, reason: str) -> None
  - [x] Use @transaction.atomic
  - [x] Add to user.token_balance
  - [x] Create TokenTransaction record (type=purchase or earn)

- [x] Implement refund_tokens with transaction (Previously implemented)
  - [x] Method signature: refund_tokens(user_id: int, amount: int, reason: str) -> None
  - [x] Use @transaction.atomic
  - [x] Add tokens back to user.token_balance
  - [x] Create TokenTransaction record (type=refund)

- [x] Concurrency testing (Commit: 13919c5)
  - [x] Write test: 20 simultaneous consume_tokens calls
  - [x] Use threading for concurrency testing
  - [x] Verify final token_balance is accurate
  - [x] Verify no race conditions (lost updates)
  - [x] Verify all transactions logged in Transaction table
  - [x] Test concurrent add and consume operations
  - [x] Test insufficient balance handling during concurrency
  - [x] Test concurrent refunds

**Implementation Reference**: [CODE_GUIDE.md#token-service](CODE_GUIDE.md#token-service)

**Exit Criteria**:
- ✅ 20 concurrent consume_tokens calls succeed without race condition
- ✅ Token balance is accurate after all transactions
- ✅ All transactions logged in Transaction table


### M2-Style-Model-API

**Referenced by**: Root PLAN.md → PT-M2-StyleAPI
**Status**: DONE

#### Subtasks

- [x] Create StyleModel serializer (Commit: 69951bd)
  - [x] Create app/serializers/style.py
  - [x] StyleListSerializer (id, name, artist, thumbnail, price, usage_count, tags)
  - [x] StyleDetailSerializer (all fields + artworks, tags, is_ready)
  - [x] StyleCreateSerializer (validation logic for images and tags)

- [x] Create StyleModelViewSet (Commit: 69951bd)
  - [x] Create app/views/style.py
  - [x] Extend BaseViewSet
  - [x] Implement list() method with filtering and sorting (inherited from BaseViewSet)
  - [x] Implement retrieve() method with detail serializer
  - [x] Implement create() method (artist-only permission)
  - [x] Implement destroy() method (owner-only permission, soft delete)

- [x] POST /api/models/ endpoint (Commit: 69951bd)
  - [x] Accept multipart/form-data with images
  - [x] Validate: 10-100 images required
  - [x] Validate: JPG/PNG only, max 10MB each
  - [x] Create placeholder for S3 upload (TODO in production)
  - [x] Create Style record (status=training after RabbitMQ submission)
  - [x] Assign tags from request
  - [x] Send training task to RabbitMQ
  - [x] Return style data with task_id

- [x] GET /api/models endpoint (Commit: 69951bd)
  - [x] Implement pagination (cursor-based, default 20 per page)
  - [x] Filter by tags: ?tags=watercolor,portrait (AND logic)
  - [x] Filter by artist: ?artist_id=123
  - [x] Filter by training_status: ?training_status=completed
  - [x] Sort by: ?sort=popular or ?sort=created_at (default: -created_at)
  - [x] Only return completed models for non-artists

- [x] GET /api/models/:id endpoint (Commit: 69951bd)
  - [x] Return full model details
  - [x] Include artist info (id, username, profile_image)
  - [x] Include artworks (training images)
  - [x] Include tags array with sequence
  - [x] Return 404 if not found

- [x] DELETE /api/models/:id endpoint (Commit: 69951bd)
  - [x] Check permission: user is owner
  - [x] Soft delete (set is_active=False)
  - [x] Return 204 No Content on success

- [x] Permissions (Commit: 69951bd)
  - [x] Create IsArtist permission
  - [x] Create IsOwnerOrReadOnly permission
  - [x] Create IsOwner permission

- [x] Testing (Commit: 69951bd)
  - [x] Test list styles (anonymous and authenticated)
  - [x] Test tag filtering (AND logic)
  - [x] Test artist filtering
  - [x] Test sorting (popularity)
  - [x] Test retrieve style detail
  - [x] Test create style requires authentication
  - [x] Test create style requires artist role
  - [x] Test insufficient images validation (< 10)
  - [x] Test duplicate name validation
  - [x] Test delete by owner (soft delete)
  - [x] Test delete by non-owner (403)
  - [x] Test artist sees own pending styles
  - [x] Test regular user only sees completed styles
  - [x] 13 tests passing, 1 skipped

**Implementation Reference**: [CODE_GUIDE.md#viewsets-and-serializers](CODE_GUIDE.md#viewsets-and-serializers)

**Exit Criteria**:
- ✅ Can create style model with image validation
- ✅ List endpoint supports filtering and sorting
- ✅ Detail endpoint returns complete information
- ✅ Permissions enforced correctly

---

### M2-Token-API

**Referenced by**: Root PLAN.md → PT-M2-TokenAPI
**Status**: DONE

#### Subtasks

- [x] Create Token serializers (Commit: 09341ab)
  - [x] TokenBalanceSerializer (balance)
  - [x] TokenPurchaseSerializer (amount, payment_method with validation)
  - [x] TokenTransactionSerializer (id, type, amount, direction, created_at, etc.)

- [x] Create TokenViewSet (Commit: 09341ab)
  - [x] Create app/views/token.py
  - [x] Use GenericViewSet (not ModelViewSet)
  - [x] Custom actions: balance, purchase, transactions

- [x] GET /api/tokens/balance/ endpoint (Commit: 09341ab)
  - [x] Return current user token_balance
  - [x] Require authentication

- [x] POST /api/tokens/purchase/ endpoint (Commit: 09341ab)
  - [x] Accept: amount (100-1,000,000, multiples of 100), payment_method
  - [x] Mock payment gateway (always success for testing)
  - [x] Call TokenService.add_tokens(user_id, amount, "purchase")
  - [x] Return new balance and transaction details

- [x] GET /api/tokens/transactions/ endpoint (Commit: 09341ab)
  - [x] List user Transaction history (sender or receiver)
  - [x] Filter by type: ?type=consume, purchase, earn, etc.
  - [x] Paginate results (cursor-based, 20 per page)
  - [x] Sort by created_at DESC
  - [x] Include direction field (incoming/outgoing/system)

- [x] Testing (Commit: 09341ab)
  - [x] Test balance endpoint requires authentication
  - [x] Test balance endpoint returns correct value
  - [x] Test purchase requires authentication
  - [x] Test purchase adds tokens and creates transaction
  - [x] Test purchase validation (min, max, multiples of 100)
  - [x] Test transactions requires authentication
  - [x] Test transactions list with pagination
  - [x] Test transactions filter by type
  - [x] Test transactions ordering (DESC)
  - [x] Test transaction direction field
  - [x] Test user only sees own transactions
  - [x] 12 tests passing

**Implementation Reference**: [CODE_GUIDE.md#custom-viewsets](CODE_GUIDE.md#custom-viewsets)

**Exit Criteria**:
- ✅ Balance endpoint works
- ✅ Purchase flow completes successfully
- ✅ Transaction history displays correctly with filtering

---

### M2-Tag-API

**Referenced by**: Root PLAN.md → PT-M2-TagAPI
**Status**: DONE

#### Subtasks

- [x] Create Tag serializer (Commit: 587e3ec)
  - [x] TagSerializer (id, name, usage_count)

- [x] Create TagViewSet (Commit: 587e3ec)
  - [x] Create app/views/tag.py
  - [x] Read-only ViewSet (list and retrieve)
  - [x] GET /api/tags/ - List popular tags (top 20)
  - [x] GET /api/tags/?search=water - Autocomplete search
  - [x] GET /api/tags/:id/ - Get tag detail

- [x] Implement AND logic for model filtering (Commit: 69951bd - completed in M2-Style-Model-API)
  - [x] Update StyleModelViewSet.get_queryset()
  - [x] ?tags=watercolor,portrait uses AND logic (both tags required)

- [x] Testing (Commit: 587e3ec)
  - [x] Test list tags (public access, popular tags only, sorted by usage_count)
  - [x] Test exclude inactive and unused tags
  - [x] Test search/autocomplete (case-insensitive, partial match)
  - [x] Test tag detail endpoint
  - [x] Test model filtering with multiple tags (AND logic)
  - [x] Test model filtering with single tag
  - [x] 11 tests passing

**Implementation Reference**: [CODE_GUIDE.md#filtering](CODE_GUIDE.md#filtering)

**Exit Criteria**:
- ✅ Popular tags endpoint works
- ✅ Autocomplete helps users find tags
- ✅ Tag filtering works correctly


## M4: AI Integration

### M4-AI-Integration

**Referenced by**: Root PLAN.md → PT-M4-Backend  
**Status**: PLANNED

#### Subtasks

- [ ] Create webhook endpoints
  - [ ] Create app/views/webhooks.py
  - [ ] PATCH /api/models/:id/status
    - [ ] Validate internal API token in header
    - [ ] Update StyleModel.training_status
    - [ ] Update StyleModel.model_path if completed
    - [ ] Update StyleModel.failure_reason if failed
  - [ ] PATCH /api/images/:id/status
    - [ ] Validate internal API token
    - [ ] Update GeneratedImage.status
    - [ ] Update GeneratedImage.image_url if completed
    - [ ] Update GeneratedImage.failure_reason if failed

- [ ] Notification creation on training events
  - [ ] POST /api/notifications endpoint
  - [ ] Create notification on training completion
    - [ ] Type: training_complete
    - [ ] Message: Your style model {name} is ready!
    - [ ] Link to model detail page
  - [ ] Create notification on training failure
    - [ ] Type: training_failed
    - [ ] Message: Training failed for {name}. {reason}

- [ ] Token refund on generation failure
  - [ ] In GeneratedImage status webhook
  - [ ] If status=failed, call TokenService.refund_tokens()
  - [ ] Refund amount = generation cost
  - [ ] Reason: generation_failed

- [ ] POST /api/images/generate endpoint
  - [ ] Accept: style_id, prompt_tags, aspect_ratio, seed (optional)
  - [ ] Validate user has sufficient tokens
  - [ ] Calculate cost based on aspect_ratio
  - [ ] Call TokenService.consume_tokens()
  - [ ] Create GeneratedImage record (status=queued)
  - [ ] Send generation task to RabbitMQ
  - [ ] Return generation_id and status

- [ ] GET /api/images/:id/status endpoint
  - [ ] Return GeneratedImage status
  - [ ] Return image_url if completed
  - [ ] Return failure_reason if failed
  - [ ] Support polling by frontend

- [ ] Internal API token authentication
  - [ ] Create middleware or decorator: @require_internal_token
  - [ ] Validate INTERNAL_API_TOKEN from settings
  - [ ] Return 403 if invalid

- [ ] Testing
  - [ ] Test webhook updates model status
  - [ ] Test notification created on training complete
  - [ ] Test token refund on generation failure
  - [ ] Test generate endpoint consumes tokens
  - [ ] Test status polling endpoint
  - [ ] Test webhook authentication

**Implementation Reference**: [CODE_GUIDE.md#webhooks](CODE_GUIDE.md#webhooks)

**Exit Criteria**:
- [ ] Webhooks update model and image status
- [ ] Notifications created on training events
- [ ] Token refunds work correctly
- [ ] Generate endpoint functional

---

## M5: Community

### M5-Notification

**Referenced by**: Root PLAN.md → CP-M5-1
**Status**: DONE

#### Subtasks

- [x] Create Notification model triggers (Commit: fd52a4c)
  - [x] Django signal on Like creation → create notification
  - [x] Django signal on Comment creation → create notification
  - [x] Django signal on Follow creation → create notification
  - [x] Create app/signals.py for signal handlers
  - [x] Prevent self-notification (user liking/commenting own content)

- [x] GET /api/notifications endpoint (Commit: fd52a4c)
  - [x] Create app/views/notification.py
  - [x] List user notifications
  - [x] Paginate (20 per page with PageNumberPagination)
  - [x] Sort by created_at DESC
  - [x] Include unread count
  - [x] Support unread_only filter query param

- [x] PATCH /api/notifications/:id/read endpoint (Commit: fd52a4c)
  - [x] Mark notification as read
  - [x] Update is_read=True
  - [x] Return updated notification
  - [x] Verify ownership (users can only mark own notifications)

- [x] Bulk mark as read endpoint (Commit: fd52a4c)
  - [x] POST /api/notifications/mark-all-read
  - [x] Update all unread notifications for current user
  - [x] Return updated count

- [x] Testing (Commit: fd52a4c)
  - [x] Test like creates notification for generation owner
  - [x] Test comment creates notification
  - [x] Test follow creates notification
  - [x] Test self-like does not create notification
  - [x] Test self-comment does not create notification
  - [x] Test notification list pagination
  - [x] Test mark as read
  - [x] Test mark all as read
  - [x] Test unread_only filtering
  - [x] Test notification ordering
  - [x] Test permissions (cannot mark other user's notifications)
  - [x] Test unauthenticated access denied
  - [x] 12 tests passing

**Implementation Reference**: [CODE_GUIDE.md#django-signals](CODE_GUIDE.md#django-signals)

**Exit Criteria**:
- ✅ Notifications created automatically on events
- ✅ Notification list displays correctly
- ✅ Mark as read works

---

### M5-Community-API

**Referenced by**: Root PLAN.md → PT-M5-CommunityBackend  
**Status**: PLANNED

#### Subtasks

- [ ] Create Feed endpoint
  - [ ] GET /api/community/feed
  - [ ] Query GeneratedImage where visibility=public
  - [ ] Use select_related(user, style_model)
  - [ ] Annotate with like_count, comment_count
  - [ ] Paginate (20 per page)
  - [ ] Sort by created_at DESC
  - [ ] Test query performance (< 200ms)

- [ ] Image detail endpoint
  - [ ] GET /api/images/:id
  - [ ] Return image with like_count, comment_count
  - [ ] Include artist info
  - [ ] Include is_liked_by_current_user field
  - [ ] Return 404 if not found or not public

- [ ] Like functionality
  - [ ] POST /api/images/:id/like
  - [ ] Toggle like (create or delete ImageLike)
  - [ ] Use get_or_create to prevent duplicates
  - [ ] Unique constraint on (user_id, image_id)
  - [ ] Return new like_count and is_liked status

- [ ] Comment endpoints
  - [ ] GET /api/images/:id/comments
    - [ ] List comments for image
    - [ ] Paginate (20 per page)
    - [ ] Sort by created_at ASC
  - [ ] POST /api/images/:id/comments
    - [ ] Create comment with content validation (max 500 chars)
    - [ ] Return created comment
  - [ ] DELETE /api/comments/:id
    - [ ] Check permission: owner or admin
    - [ ] Delete comment
    - [ ] Return 204 No Content

- [ ] Follow functionality
  - [ ] POST /api/artists/:id/follow
  - [ ] Toggle follow (create or delete Follow)
  - [ ] Unique constraint on (follower_id, following_id)
  - [ ] Return is_following status

- [ ] GET /api/users/following endpoint
  - [ ] List artists current user is following
  - [ ] Include artist info and follower_count
  - [ ] Paginate results

- [ ] Testing
  - [ ] Test feed query performance with 1000 images
  - [ ] Test like toggle works correctly
  - [ ] Test duplicate like prevention
  - [ ] Test comment creation and deletion
  - [ ] Test follow toggle
  - [ ] Test permissions on delete comment

**Implementation Reference**: [CODE_GUIDE.md#community-features](CODE_GUIDE.md#community-features)

**Exit Criteria**:
- [ ] Feed loads quickly (< 200ms)
- [ ] Like/comment/follow functionality works
- [ ] Permissions enforced correctly


## M6: Launch

### M6-Performance

**Referenced by**: Root PLAN.md → CP-M6-2  
**Status**: PLANNED

#### Subtasks

- [ ] Set up load testing
  - [ ] Install k6 or Locust
  - [ ] Write test scenario: browse models → view detail → generate image
  - [ ] Configure 100 concurrent virtual users

- [ ] Run load tests and measure
  - [ ] Measure API response times (p50, p95, p99)
  - [ ] Measure database query times
  - [ ] Measure RabbitMQ message throughput
  - [ ] Monitor system resources (CPU, RAM, DB connections)

- [ ] Identify bottlenecks
  - [ ] Check for N+1 queries with Django Debug Toolbar
  - [ ] Check for slow database queries (> 100ms)
  - [ ] Check for memory leaks
  - [ ] Check for connection pool exhaustion

- [ ] Optimize slow queries
  - [ ] Add database indexes on frequently queried fields
    - [ ] Index on StyleModel(created_at, training_status)
    - [ ] Index on GeneratedImage(user_id, created_at)
    - [ ] Index on TokenTransaction(user_id, created_at)
  - [ ] Use select_related and prefetch_related
  - [ ] Add database query result caching where appropriate

- [ ] Implement caching
  - [ ] Install django-redis
  - [ ] Cache popular models list (5 min TTL)
  - [ ] Cache tag list (10 min TTL)
  - [ ] Cache user token balance (1 min TTL, invalidate on transaction)

- [ ] Re-run load tests
  - [ ] Verify p95 response time < 500ms
  - [ ] Verify system handles 100 concurrent users
  - [ ] Verify no errors under load

**Implementation Reference**: [CODE_GUIDE.md#performance-optimization](CODE_GUIDE.md#performance-optimization)

**Exit Criteria**:
- [ ] p95 API response time < 500ms
- [ ] System handles 100 concurrent users without errors
- [ ] No N+1 query issues

---

### M6-Production-Config

**Referenced by**: Root PLAN.md → PT-M6-BackendDeploy  
**Status**: PLANNED

#### Subtasks

- [ ] Production settings configuration
  - [ ] Create config/settings_production.py
  - [ ] Set DEBUG=False
  - [ ] Configure ALLOWED_HOSTS from environment variable
  - [ ] Set SECRET_KEY from environment (never hardcode)
  - [ ] Configure SECURE_SSL_REDIRECT=True
  - [ ] Configure SECURE_HSTS_SECONDS=31536000
  - [ ] Configure SESSION_COOKIE_SECURE=True
  - [ ] Configure CSRF_COOKIE_SECURE=True

- [ ] Static files configuration
  - [ ] Install whitenoise for static file serving
  - [ ] Configure STATIC_ROOT=/app/staticfiles
  - [ ] Run collectstatic in Dockerfile
  - [ ] Alternative: upload to S3 and use CloudFront

- [ ] Gunicorn configuration
  - [ ] Create gunicorn.conf.py
  - [ ] Set workers = (CPU cores * 2) + 1
  - [ ] Set timeout = 120 seconds
  - [ ] Configure access and error logs
  - [ ] Set bind = 0.0.0.0:8000

- [ ] Nginx reverse proxy
  - [ ] Verify nginx/conf.d/default.conf configuration
  - [ ] Configure proxy_pass to backend:8000
  - [ ] Configure static file serving at /static/
  - [ ] Configure media file serving at /media/
  - [ ] Set proper headers (X-Forwarded-For, X-Real-IP)

- [ ] Database connection pooling
  - [ ] Configure CONN_MAX_AGE in DATABASES setting
  - [ ] Set CONN_MAX_AGE = 600 (10 minutes)
  - [ ] Monitor connection pool usage

- [ ] Environment variable validation
  - [ ] Create script to check all required env vars on startup
  - [ ] Required: SECRET_KEY, DATABASE_URL, AWS_ACCESS_KEY_ID, etc.
  - [ ] Fail fast if any required var is missing

- [ ] Testing
  - [ ] Test production build locally
  - [ ] Test with DEBUG=False
  - [ ] Test static files serve correctly
  - [ ] Test Gunicorn handles concurrent requests

**Implementation Reference**: [CODE_GUIDE.md#production-deployment](CODE_GUIDE.md#production-deployment)

**Exit Criteria**:
- [ ] Production settings configured correctly
- [ ] Static files serve properly
- [ ] Gunicorn runs stably
- [ ] All security headers set

---

## Quick Reference

### Task Status Tracking

When completing subtasks:
1. Mark subtask with [x] in this file
2. Update corresponding task in root PLAN.md when all subtasks done
3. Run tests to verify completion
4. Document any deviations or issues

### File Locations

Based on [README.md Directory Structure](README.md#directory-structure):

```
app/
├── models/          # Django models (user.py, style_model.py, etc.)
├── serializers/     # DRF serializers
├── views/           # ViewSets and API views
├── services/        # Business logic (token_service.py, rabbitmq_service.py)
├── tests/           # Unit and integration tests
├── migrations/      # Database migrations
├── exceptions.py    # Custom exception handlers
├── signals.py       # Django signal handlers
└── urls.py          # URL routing
```

### Common Commands

```bash
# Development
python manage.py runserver
python manage.py makemigrations
python manage.py migrate
python manage.py test

# Code quality
black app/
pylint app/
python manage.py check

# Production
python manage.py collectstatic --noinput
gunicorn config.wsgi:application
```

---

**Note**: This plan is a living document. Update it as you complete tasks and encounter new requirements.
