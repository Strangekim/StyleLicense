# Common Code Patterns

**목적**: 프로젝트 전체에서 일관되게 사용하는 공통 패턴과 규칙을 정의합니다.  
**범위**: Backend, Frontend, AI 서버 모두 적용  
**참고**: 각 앱의 세부 패턴은 `apps/*/CODE_GUIDE.md` 참조

---

## 목차
1. [API Response Format](#1-api-response-format)
2. [Error Handling](#2-error-handling)
3. [HTTP Status Codes](#3-http-status-codes)
4. [Naming Conventions](#4-naming-conventions)
5. [Data Types & Formats](#5-data-types--formats)
6. [Pagination](#6-pagination)
7. [RabbitMQ Message Format](#7-rabbitmq-message-format)
8. [Database Conventions](#8-database-conventions)
9. [Git Commit Convention](#9-git-commit-convention)

---

## 1. API Response Format

### 1.1 Success Response (Collection with Pagination)

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 123,
        "name": "Watercolor Dreams",
        "artist_name": "John Doe"
      }
    ],
    "next_cursor": "2025-01-15T10:20:30Z",
    "has_more": true
  }
}
```

**규칙**:
- 모든 성공 응답은 `{success: true, data: {...}}` 형식
- `data` 안에 실제 리소스 데이터 포함
- Cursor 기반 페이지네이션 사용:
  - `results`: 리소스 배열 (복수형)
  - `next_cursor`: 다음 페이지 커서 (ISO 8601). `null`이면 마지막 페이지
  - `has_more`: 다음 페이지 존재 여부
- ⚠️ 전체 개수(`count`)는 성능상 제공하지 않음

### 1.2 Success Response (Single Entity)

```json
{
  "success": true,
  "data": {
    "id": 123,
    "name": "Watercolor Dreams",
    "description": "A beautiful watercolor style",
    "status": "COMPLETED",
    "generation_cost_tokens": 100,
    "artist_name": "John Doe",
    "created_at": "2025-01-15T10:30:00.000Z",
    "updated_at": "2025-01-20T14:45:00.000Z"
  }
}
```

**규칙**:
- `success: true` 필드로 성공 여부 명시
- `data` 객체에 entity 필드 배치

### 1.3 Success Response (CREATE)

```http
POST /api/styles/
HTTP/1.1 201 Created
Location: /api/styles/123
Content-Type: application/json

{
  "success": true,
  "data": {
    "id": 123,
    "name": "New Style",
    "status": "DRAFT",
    "created_at": "2025-01-20T10:00:00.000Z"
  }
}
```

**규칙**:
- HTTP `201 Created` 반환
- `Location` 헤더에 생성된 리소스 URL 포함
- `{success: true, data: {...}}` 형식으로 entity 반환

### 1.4 Success Response (DELETE)

```http
DELETE /api/styles/123
HTTP/1.1 204 No Content
```

**규칙**:
- HTTP `204 No Content` 반환
- Response body **비어있음**

---

## 2. Error Handling

### 2.1 Error Response Format

```json
{
  "success": false,
  "error": {
    "code": "INSUFFICIENT_TOKENS",
    "message": "토큰 잔액이 부족합니다",
    "details": {
      "required": 100,
      "available": 50
    }
  }
}
```

**필드 설명**:
- `success` (boolean): 항상 `false`
- `error` (object): 에러 정보
  - `code` (string): 에러 코드 (대문자 SNAKE_CASE)
  - `message` (string): 사용자에게 표시할 메시지 (다국어 지원)
  - `details` (object|null): 추가 디버깅 정보 (선택사항)

### 2.2 Validation Error (422)

```http
POST /api/styles/
HTTP/1.1 422 Unprocessable Entity

{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "입력값 검증에 실패했습니다",
    "details": {
      "generation_cost_tokens": "이미지당 가격은 최소 10토큰이어야 합니다",
      "name": "스타일 이름은 필수입니다"
    }
  }
}
```

**특징**:
- 여러 validation 에러를 `details` 객체에 필드명별로 정리
- 각 필드의 에러 메시지를 사용자 친화적으로 제공

### 2.3 Common Error Codes

| HTTP Status | Error Code | 설명 |
|------------|------------|------|
| 400 | `INVALID_REQUEST` | 요청 형식 오류 (malformed JSON 등) |
| 401 | `UNAUTHORIZED` | 인증 필요 |
| 403 | `FORBIDDEN` | 권한 부족 |
| 404 | `NOT_FOUND` | 리소스 없음 |
| 409 | `CONFLICT` | 리소스 충돌 (중복 생성 등) |
| 422 | `VALIDATION_ERROR` | 입력 검증 실패 |
| 402 | `INSUFFICIENT_TOKENS` | 토큰 부족 |
| 422 | `TRAINING_IN_PROGRESS` | 이미 학습 중 |
| 429 | `RATE_LIMIT_EXCEEDED` | 요청 횟수 초과 |
| 500 | `INTERNAL_SERVER_ERROR` | 서버 오류 |
| 503 | `SERVICE_UNAVAILABLE` | 서비스 일시 중단 |

### 2.4 Trace ID Header

**모든 응답**에 `X-Trace-Id` 헤더 포함 (디버깅 및 로깅용):

```http
HTTP/1.1 500 Internal Server Error
X-Trace-Id: 550e8400-e29b-41d4-a716-446655440000
Content-Type: application/json

{
  "success": false,
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "일시적인 오류가 발생했습니다. 잠시 후 다시 시도해주세요",
    "details": null
  }
}
```

---

## 3. HTTP Status Codes

### 3.1 Success Responses

| Status Code | 용도 | 예시 |
|------------|------|------|
| `200 OK` | 성공 (GET, PUT, PATCH) | 리스트 조회, 수정 완료 |
| `201 Created` | 생성 성공 (POST) | 스타일 생성 |
| `202 Accepted` | 비동기 처리 수락 | 학습/생성 요청 |
| `204 No Content` | 성공 (body 없음) | DELETE 성공 |
| `304 Not Modified` | 캐싱 (ETag) | 변경사항 없음 |

### 3.2 Client Error Responses

| Status Code | 용도 | 예시 |
|------------|------|------|
| `400 Bad Request` | 요청 형식 오류 | Malformed JSON |
| `401 Unauthorized` | 인증 필요 | 로그인 안 됨 |
| `403 Forbidden` | 권한 부족 | 작가 전용 API |
| `404 Not Found` | 리소스 없음 | 존재하지 않는 스타일 |
| `405 Method Not Allowed` | HTTP 메서드 불허 | POST /api/styles/123 |
| `406 Not Acceptable` | Accept 헤더 오류 | 지원하지 않는 형식 |
| `410 Gone` | 리소스 영구 삭제 | 구 API 버전 |
| `415 Unsupported Media Type` | Content-Type 오류 | XML 전송 |
| `422 Unprocessable Entity` | Validation 실패 | 필드 검증 오류 |
| `429 Too Many Requests` | Rate Limit 초과 | 요청 횟수 제한 |

### 3.3 Server Error Responses

| Status Code | 용도 | 예시 |
|------------|------|------|
| `500 Internal Server Error` | 서버 오류 | DB 연결 실패 |
| `501 Not Implemented` | 미구현 기능 | 개발 중 |
| `502 Bad Gateway` | Upstream 오류 | AI 서버 응답 없음 |
| `503 Service Unavailable` | 서비스 중단 | 점검 중 |
| `504 Gateway Timeout` | Timeout | AI 서버 응답 지연 |

---

## 4. Naming Conventions

### 4.1 URL Paths

**규칙**:
- **소문자** 사용
- 단어 구분은 **하이픈(-)** 사용
- **복수형** 리소스명 사용

```
✅ Good:
/api/styles
/api/generations
/api/transactions

❌ Bad:
/api/Style
/api/generated_images
/api/tokenTransaction
/api/post
```

### 4.2 JSON Property Names

**규칙**:
- **snake_case** 사용 (Python/Django 백엔드와 일관성)
- 배열은 **복수형**, 단일 값은 **단수형**

```json
{
  "user_id": "123",
  "first_name": "John",
  "last_name": "Doe",
  "styles": [
    {"id": "1", "name": "Style 1"}
  ],
  "total_count": 10,
  "styles_count": 3,
  "is_active": true
}
```

```
✅ Good:
first_name, last_name, generation_cost_tokens, created_at

❌ Bad:
firstName, FirstName, pricePerImage, createdAt
```

### 4.3 Query Parameters

**규칙**:
- **snake_case** 사용 (JSON property와 일관성 유지)
- 소문자만 사용

```
✅ Good:
GET /api/styles?cursor=2025-01-15T12:34:56Z&limit=20&sort=recent&artist_id=123

❌ Bad:
GET /api/styles?Cursor=xxx&LIMIT=20&Sort=recent&artistId=123  # Inconsistent casing
```

### 4.4 Error Codes

**규칙**:
- **대문자 SNAKE_CASE** 사용
- 명확하고 구체적인 이름

```
✅ Good:
INSUFFICIENT_TOKENS
TRAINING_IN_PROGRESS
INVALID_IMAGE_FORMAT
DUPLICATE_STYLE_NAME

❌ Bad:
insufficientTokens
training-in-progress
ERROR_001
```

---

## 5. Data Types & Formats

### 5.1 ID (Identifier)

**형식**: Integer (BIGINT)

```json
{
  "id": 123,
  "style_id": 456
}
```

### 5.2 Date & Time

**형식**: ISO 8601, UTC 기준

```json
{
  "created_at": "2025-01-20T10:30:45.123Z",
  "updated_at": "2025-01-20T14:00:00.000Z",
  "scheduled_at": "2025-02-01T00:00:00.000Z"
}
```

**Time Only** (날짜 없이 시간만):

```json
{
  "open_time": "09:00:00.000",
  "close_time": "18:00:00.000"
}
```

### 5.3 Price & Currency

**형식**: 객체 형태 (amount + currency)

```json
{
  "price": {
    "amount": "1250.50",
    "currency": "KRW"
  },
  "discount": {
    "amount": "100.00",
    "currency": "KRW"
  }
}
```

**규칙**:
- `amount`: 문자열, 소수점 `.` 사용, 최대 2자리
- `currency`: ISO 4217 3글자 코드

```json
{
  "amount": "0.00",     // ✅
  "amount": "11.25",    // ✅
  "amount": "1234567.99" // ✅
}
```

### 5.4 Country & Language Codes

**Country**: ISO 3166 Alpha-2 (2글자, 대문자)

```json
{
  "country_code": "KR",
  "shipping_address": {
    "city": "Seoul",
    "country_code": "KR"
  }
}
```

**Language**: RFC 5646 (언어-국가)

```json
{
  "preferred_language": "ko-KR",
  "supported_languages": ["en-US", "ko-KR", "ja-JP"]
}
```

### 5.5 Null & Empty Collections

**Null 값**: 알 수 없거나 선택사항인 필드는 `null`

```json
{
  "middle_name": null,
  "description": null,
  "model_file_url": null
}
```

**Empty Collections**: 빈 배열 `[]` 사용 (절대 `null` 사용 금지)

```json
{
  "styles": [],
  "errors": [],
  "tags": []
}
```

### 5.6 Boolean

**규칙**: `is_` 또는 `has_` 접두사 사용 (snake_case)

```json
{
  "is_active": true,
  "is_public": false,
  "has_model": true,
  "is_training": false
}
```

---

## 6. Pagination

### 6.1 Cursor-based Pagination (권장)

프로젝트에서는 **Cursor-based pagination**을 사용합니다.

**Query Parameters**:
- `cursor`: 다음 페이지 커서 (ISO 8601 datetime, 선택사항)
- `limit`: 결과 수 (1-100, 기본값 20)

```http
GET /api/generations?limit=20
GET /api/generations?cursor=2025-01-15T12:34:56Z&limit=20
```

**Response**:

```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 123,
        "title": "게시글 제목",
        "created_at": "2025-01-15T12:34:56Z"
      }
    ],
    "next_cursor": "2025-01-15T10:20:30Z",
    "has_more": true
  }
}
```

**필드 설명**:
- `results`: 리소스 배열
- `next_cursor` (string|null): 다음 페이지 커서 (ISO 8601). `null`이면 마지막 페이지
- `has_more` (boolean): 다음 페이지 존재 여부

**장점**:
- 무한 스크롤에 적합
- 데이터 변경 시에도 안정적
- 성능 우수 (offset보다 빠름)

---

## 7. RabbitMQ Message Format

### 7.1 Training Task

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "type": "model_training",
  "data": {
    "style_id": 123,
    "images": [
      "s3://bucket/training/image1.jpg",
      "s3://bucket/training/image2.jpg"
    ],
    "tags": ["watercolor", "portrait", "vintage"],
    "parameters": {
      "epochs": 200,
      "learning_rate": 0.0001,
      "batch_size": 4
    }
  },
  "callback_url": "https://api.stylelicense.com/api/webhooks/training/complete",
  "created_at": "2025-01-20T10:00:00.000Z"
}
```

### 7.2 Image Generation Task

```json
{
  "task_id": "660f9511-f3ac-52e5-b827-557766551111",
  "type": "image_generation",
  "data": {
    "generation_id": 456,
    "style_id": 123,
    "prompt": "a beautiful sunset over mountains, watercolor style",
    "negative_prompt": "blurry, low quality",
    "parameters": {
      "width": 512,
      "height": 512,
      "steps": 50,
      "cfg_scale": 7.5,
      "seed": 42
    }
  },
  "callback_url": "https://api.stylelicense.com/api/webhooks/inference/complete",
  "created_at": "2025-01-20T11:30:00.000Z"
}
```

### 7.3 Progress Update (Webhook)

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "processing",
  "progress": 45,
  "current_step": 90,
  "total_steps": 200,
  "estimated_seconds_remaining": 180,
  "message": "Training in progress",
  "updated_at": "2025-01-20T10:15:00.000Z"
}
```

### 7.4 Task Completion (Webhook)

**Success**:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "completed",
  "success": true,
  "data": {
    "style_id": 123,
    "model_file_url": "s3://bucket/models/style-123.safetensors",
    "training_logs": "s3://bucket/logs/style-123.log"
  },
  "completed_at": "2025-01-20T10:30:00.000Z"
}
```

**Failure**:

```json
{
  "task_id": "550e8400-e29b-41d4-a716-446655440000",
  "status": "failed",
  "success": false,
  "error": {
    "code": "TRAINING_FAILED",
    "message": "CUDA out of memory",
    "details": "RuntimeError at step 45"
  },
  "completed_at": "2025-01-20T10:15:00.000Z"
}
```

### 7.5 Webhook Authentication

AI 서버(Training/Inference)에서 Backend로 보내는 **모든 webhook 요청**은 인증이 필요합니다.

**Request Header**:

```http
POST /api/webhooks/training/complete
Authorization: Bearer <INTERNAL_API_TOKEN>
X-Request-Source: training-server
Content-Type: application/json
```

**환경변수**:
- Backend: `INTERNAL_API_TOKEN` (검증용)
- AI Servers: `INTERNAL_API_TOKEN` (전송용, 동일한 값)

**인증 실패 시**:

```http
HTTP/1.1 401 Unauthorized

{
  "success": false,
  "error": {
    "code": "UNAUTHORIZED",
    "message": "Invalid or missing Authorization header",
    "details": null
  }
}
```

**보안 규칙**:
- `Authorization: Bearer` 헤더 사용 (표준 OAuth2 방식)
- `X-Request-Source` 헤더로 요청 출처 명시 (training-server | inference-server)
- `INTERNAL_API_TOKEN`은 환경변수로만 관리 (코드에 하드코딩 금지)
- 최소 32자 이상의 UUID 또는 랜덤 문자열 사용
- IP 화이트리스트: AI 서버 IP만 허용
- HTTPS 연결에서만 사용 (개발환경 제외)

---

## 8. Database Conventions

### 8.1 Table Names

**규칙**:
- 소문자 `snake_case`
- **복수형** 사용

```
✅ Good:
users
styles
token_transactions
generated_images
community_posts

❌ Bad:
User
style
TokenTransaction
generatedImage
```

### 8.2 Column Names

**규칙**:
- 소문자 `snake_case`
- Boolean은 `is_` 또는 `has_` 접두사

```sql
CREATE TABLE styles (
    id UUID PRIMARY KEY,
    artist_id UUID NOT NULL,
    name VARCHAR(200) NOT NULL,
    description TEXT,
    generation_cost_tokens INTEGER DEFAULT 100,
    is_active BOOLEAN DEFAULT TRUE,
    is_public BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ NOT NULL,
    updated_at TIMESTAMPTZ NOT NULL
);
```

### 8.3 Foreign Keys

**규칙**:
- `{related_table}_id` 형식

```sql
-- users 테이블 참조
artist_id UUID REFERENCES users(id)
user_id UUID REFERENCES users(id)

-- styles 테이블 참조
style_id BIGINT REFERENCES styles(id)
```

### 8.4 Index Names

**규칙**:
- `idx_{table}_{column(s)}` 형식

```sql
CREATE INDEX idx_users_email ON users(email);
CREATE INDEX idx_users_provider_userid ON users(provider, provider_user_id);
CREATE INDEX idx_styles_artist_status ON styles(artist_id, status);
CREATE INDEX idx_generations_user_createdat ON generations(user_id, created_at DESC);
```

### 8.5 Constraint Names

```sql
-- Primary Key: pk_{table}
CONSTRAINT pk_users PRIMARY KEY (id)

-- Foreign Key: fk_{table}_{column}_{ref_table}
CONSTRAINT fk_styles_artist_users
    FOREIGN KEY (artist_id) REFERENCES users(id)

-- Unique: uk_{table}_{column(s)}
CONSTRAINT uk_users_email UNIQUE (email)
CONSTRAINT uk_users_provider_userid UNIQUE (provider, provider_user_id)

-- Check: ck_{table}_{column}_{condition}
CONSTRAINT ck_styles_price_positive
    CHECK (generation_cost_tokens > 0)
```

---

## 9. Git Commit Convention

### 9.1 Commit Message Format

```
<type>(<scope>): <subject>

<body>

<footer>
```

### 9.2 Types

| Type | 설명 | 예시 |
|------|------|------|
| `feat` | 새 기능 | `feat(api): Add style search endpoint` |
| `fix` | 버그 수정 | `fix(token): Resolve race condition in consume_tokens` |
| `docs` | 문서 변경 | `docs: Update API.md with pagination examples` |
| `style` | 코드 포맷팅 | `style: Run black on backend` |
| `refactor` | 리팩토링 | `refactor(service): Extract signature logic to service` |
| `test` | 테스트 추가/수정 | `test(token): Add concurrency tests` |
| `chore` | 빌드/설정 변경 | `chore: Update Django to 4.2.11` |
| `perf` | 성능 개선 | `perf(query): Add select_related to styles API` |

### 9.3 Scope

앱 또는 기능 단위:
- `api`, `backend`, `frontend`
- `auth`, `token`, `style`, `generation`, `community`
- `training`, `inference`
- `db`, `docs`, `deploy`

### 9.4 Examples

```
feat(style): Add training progress tracking API

- Add training_progress field to StyleModel
- Implement GET /api/styles/:id/progress endpoint
- Add WebSocket support for real-time updates

Closes #123
```

```
fix(token): Resolve race condition in consume_tokens

Use SELECT FOR UPDATE to prevent concurrent token consumption
leading to negative balance.

Fixes #456
```

```
docs(database): Update TABLES.md with new indexes

- Add composite index on (artist_id, status)
- Document index naming conventions
```

```
refactor(generation): Extract RabbitMQ logic to service

- Create RabbitMQService class
- Move publish_generation_task to service layer
- Add unit tests for RabbitMQService
```

---

## 10. API Versioning (Future)

### 10.1 Header-based Versioning

**현재**: 버전 없음 (v1 암시적 사용)

**향후 계획**: Custom Media Type 사용

```http
Accept: application/vnd.stylelicense.v1+json
Content-Type: application/vnd.stylelicense.v1+json
```

**Public API**:
```http
Accept: application/vnd.stylelicense.public.v1+json
```

**Beta API**:
```http
Accept: application/vnd.stylelicense.beta.v1+json
```

### 10.2 Version Deprecation

**Deprecated 버전**: HTTP `410 Gone` 반환

```http
GET /api/old-endpoint
HTTP/1.1 410 Gone

{
  "success": false,
  "error": {
    "code": "API_VERSION_DEPRECATED",
    "message": "이 API 버전은 더 이상 지원되지 않습니다",
    "details": {
      "newEndpoint": "/api/v2/new-endpoint"
    }
  }
}
```

---

## 11. Security Headers

### 11.1 Request Headers

**필수 헤더**:

```http
Cookie: sessionid=abc123...
X-CSRF-Token: xyz789...  # POST/PUT/PATCH/DELETE만
Content-Type: application/json
Accept: application/json
User-Agent: StyleLicense-Web/1.0.0 (ko-KR)
```

**선택 헤더**:

```http
Accept-Language: ko-KR
X-Request-ID: 550e8400-e29b-41d4-a716-446655440000
```

### 11.2 Response Headers

**보안 헤더**:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

**CORS 헤더**:

```http
Access-Control-Allow-Origin: https://stylelicense.com
Access-Control-Allow-Methods: GET, POST, PUT, PATCH, DELETE
Access-Control-Allow-Headers: Content-Type, Authorization
Access-Control-Max-Age: 86400
```

---

## 12. Rate Limiting

### 12.1 Rate Limit Headers

```http
HTTP/1.1 200 OK
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 75
X-RateLimit-Reset: 1643040000
```

### 12.2 Rate Limit Exceeded

```http
HTTP/1.1 429 Too Many Requests
Retry-After: 45
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 0
X-RateLimit-Reset: 1643040045

{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "요청 횟수를 초과했습니다. 45초 후 다시 시도해주세요",
    "details": {
      "limit": 100,
      "window": "1 minute",
      "retryAfter": 45
    }
  }
}
```

---

## 참고 자료

- **[Allegro REST API Guidelines](https://github.com/allegro/restapi-guideline)** - REST API 모범 사례
- **[RFC 7231](https://tools.ietf.org/html/rfc7231)** - HTTP/1.1 Semantics
- **[RFC 7807](https://tools.ietf.org/html/rfc7807)** - Problem Details for HTTP APIs
- **[ISO 8601](https://www.iso.org/iso-8601-date-and-time-format.html)** - Date and Time Format
- **[ISO 4217](https://www.iso.org/iso-4217-currency-codes.html)** - Currency Codes
- **[ISO 3166](https://www.iso.org/iso-3166-country-codes.html)** - Country Codes

---

**문서 버전**: 2.0  
**최종 수정**: 2025-10-30  
**작성자**: Development Team