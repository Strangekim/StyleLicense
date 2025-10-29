# API 명세서 (API.md)

**Project**: Style License  
**API Version**: v1  
**Base URL**: `https://api.stylelicense.com/v1`  
**Last Updated**: 2025-10-29

---

## 📚 문서 구조 안내

이 문서는 각 API 그룹별로 독립적으로 읽을 수 있도록 구성되어 있습니다.

| 섹션 | 내용 | 언제 읽어야 하나? |
|------|------|----------------|
| [1. 개요](#1-개요) | 공통 규칙, 응답 형식 | 프로젝트 시작 시 1회 |
| [2. 인증 API](#2-인증-api) | OAuth, 로그인/로그아웃 | M1 인증 구현 시 |
| [3. 사용자 API](#3-사용자-api) | 프로필, 작가 신청 | M2 사용자 기능 구현 시 |
| [4. 토큰 API](#4-토큰-api) | 잔액, 구매, 거래내역 | M2 토큰 시스템 구현 시 |
| [5. 스타일 API](#5-스타일-api) | 화풍 생성/조회/수정 | M2 스타일 기능 구현 시 |
| [6. 생성 API](#6-생성-api) | 이미지 생성 요청/조회 | M4 이미지 생성 구현 시 |
| [7. 커뮤니티 API](#7-커뮤니티-api) | 팔로우, 좋아요, 댓글 | M5 커뮤니티 구현 시 |
| [8. 검색 API](#8-검색-api) | 통합 검색 | M5 검색 기능 구현 시 |
| [9. 알림 API](#9-알림-api) | 알림 목록/읽음 처리 | M5 알림 기능 구현 시 |
| [10. Webhook API](#10-webhook-api) | 내부 서버 간 통신 | M4 AI 통합 시 |
| [11. 에러 코드](#11-에러-코드) | 전체 에러 코드 목록 | 에러 처리 구현 시 참조 |
| [12. Rate Limiting](#12-rate-limiting) | 요청 제한 정책 | 성능 최적화 시 참조 |

---

## 목차

1. [개요](#1-개요)
2. [인증 API](#2-인증-api)
3. [사용자 API](#3-사용자-api)
4. [토큰 API](#4-토큰-api)
5. [스타일 API](#5-스타일-api)
6. [생성 API](#6-생성-api)
7. [커뮤니티 API](#7-커뮤니티-api)
8. [검색 API](#8-검색-api)
9. [알림 API](#9-알림-api)
10. [Webhook API](#10-webhook-api)
11. [에러 코드](#11-에러-코드)
12. [Rate Limiting](#12-rate-limiting)

---

## 1. 개요

### 1.1 공통 규칙

#### Base URL (호스트만 포함)
- **개발**: `http://localhost:8000`
- **프로덕션**: `https://api.stylelicense.com`

#### 엔드포인트 경로
모든 엔드포인트는 `/api/v1/...` 형식으로 시작합니다.

**전체 URL = Base URL + 엔드포인트 경로**

예시:
- 개발: `http://localhost:8000/api/v1/auth/me`
- 프로덕션: `https://api.stylelicense.com/api/v1/auth/me`

#### 인증
- **방식**: 세션 쿠키 기반
- **헤더**: 
  ```http
  Cookie: sessionid=abc123...
  X-CSRFToken: xyz789...  # POST/PUT/PATCH/DELETE만
  ```

#### Content-Type
```http
Content-Type: application/json
```

### 1.2 응답 형식

#### 성공 응답
```json
{
  "success": true,
  "data": {
    "id": 123,
    "field": "value"
  }
}
```

#### 에러 응답
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

#### 페이지네이션 응답 (Cursor-based)
```json
{
  "success": true,
  "data": {
    "results": [...],
    "next_cursor": "2025-01-15T12:34:56Z",
    "has_more": true
  }
}
```

**쿼리 파라미터**:
- `cursor`: 다음 페이지 커서 (ISO 8601 datetime)
- `limit`: 결과 수 (1-100, 기본값 20)

### 1.3 타임스탬프 형식
모든 날짜/시간은 **ISO 8601 형식** 사용:
```
2025-01-15T12:34:56Z
```

---

## 2. 인증 API

### 2.1 Google OAuth 로그인 시작

#### Request
```http
GET /api/auth/google/login
```

#### Response
```
302 Redirect → Google OAuth Consent Screen
```

#### 설명
- 사용자를 Google OAuth 동의 화면으로 리다이렉트
- 인증 없이 접근 가능

---

### 2.2 Google OAuth 콜백

#### Request
```http
GET /api/auth/google/callback?code=...&state=...
```

#### Response
```
302 Redirect → Frontend (/)
Set-Cookie: sessionid=...; HttpOnly; Secure; SameSite=Lax
```

#### 설명
- Google이 인증 코드와 함께 호출
- Backend에서 세션 쿠키 설정 후 프론트엔드로 리다이렉트
- **신규 사용자 처리**:
  1. `users` 테이블에 레코드 생성 (`token_balance=100`)
  2. `transactions` 테이블에 웰컴 보너스 기록:
     - `sender_id`: NULL (플랫폼)
     - `receiver_id`: 신규 사용자 ID
     - `amount`: 100
     - `status`: 'completed'
     - `memo`: 'Welcome Bonus'
     - `related_generation_id`: NULL

---

### 2.3 현재 사용자 정보 조회

#### Request
```http
GET /api/auth/me
```

#### Response
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "john_doe",
    "profile_image": "https://s3.../profile.jpg",
    "role": "user",
    "token_balance": 150,
    "bio": null,
    "created_at": "2025-01-01T00:00:00Z",
    "artist": null
  }
}
```

**role='artist'인 경우**:
```json
{
  "artist": {
    "id": 10,
    "artist_name": "John Artist",
    "signature_image_url": "https://s3.../signature.png",
    "verified_email": "john@example.com",
    "earned_token_balance": 500,
    "follower_count": 123
  }
}
```

#### 에러
- `401 UNAUTHORIZED`: 로그인 필요

---

### 2.4 로그아웃

#### Request
```http
POST /api/auth/logout
X-CSRFToken: xyz789...
```

#### Response
```json
{
  "success": true,
  "message": "로그아웃되었습니다"
}
```

#### 설명
- 세션 쿠키 삭제
- 프론트엔드는 `/login`으로 리다이렉트

---

## 3. 사용자 API

### 3.1 사용자 프로필 조회

#### Request
```http
GET /api/users/:id
```

#### Response
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "john_doe",
    "profile_image": "https://s3.../profile.jpg",
    "bio": "안녕하세요!",
    "role": "artist",
    "created_at": "2025-01-01T00:00:00Z",
    "artist": {
      "id": 10,
      "artist_name": "John Artist",
      "follower_count": 123
    },
    "stats": {
      "total_generations": 50,
      "public_generations": 30,
      "following_count": 45
    }
  }
}
```

#### 에러
- `404 NOT_FOUND`: 사용자 없음

---

### 3.2 내 프로필 수정

#### Request
```http
PATCH /api/users/me
Content-Type: application/json
X-CSRFToken: xyz789...

{
  "username": "new_name",
  "bio": "새로운 소개"
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "id": 1,
    "username": "new_name",
    "bio": "새로운 소개",
    "updated_at": "2025-01-15T12:00:00Z"
  }
}
```

#### 에러
- `401 UNAUTHORIZED`: 로그인 필요
- `422 VALIDATION_ERROR`: 유효성 검증 실패

---

### 3.3 작가 권한 신청

#### Request
```http
POST /api/users/me/upgrade-to-artist
Content-Type: application/json
X-CSRFToken: xyz789...

{
  "artist_name": "John Artist",
  "verified_email": "john@example.com",
  "signature_image": "data:image/png;base64,..."
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "user": {
      "id": 1,
      "role": "artist"
    },
    "artist": {
      "id": 10,
      "artist_name": "John Artist",
      "verified_email": "john@example.com",
      "signature_image_url": "https://s3.../signature.png"
    }
  }
}
```

#### 에러
- `401 UNAUTHORIZED`: 로그인 필요
- `409 CONFLICT`: 이미 작가 권한 보유

---

## 4. 토큰 API

### 4.1 토큰 잔액 조회

#### Request
```http
GET /api/tokens/balance
```

#### Response
```json
{
  "success": true,
  "data": {
    "user_id": 1,
    "token_balance": 150,
    "artist_earned_balance": 500
  }
}
```

#### 설명
- `token_balance`: 사용 가능한 토큰 (사용자)
- `artist_earned_balance`: 작가가 벌어들인 토큰 (작가만, 현금화 대기 중)

---

### 4.2 토큰 거래 내역 조회 (통합)

#### Request
```http
GET /api/tokens/transactions?type=all&cursor=...&limit=20
```

**쿼리 파라미터**:
- `type`: `all` (기본값), `purchase` (충전), `usage` (사용)
- `cursor`: 페이지네이션 커서
- `limit`: 결과 수 (1-100, 기본값 20)

#### Response
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 100,
        "type": "purchase",
        "amount": 100,
        "price_per_token": 100.00,
        "total_price": 10000.00,
        "currency_code": "KRW",
        "status": "completed",
        "memo": "토큰 구매",
        "created_at": "2025-01-15T10:00:00Z",
        "sender": null,
        "receiver": {
          "id": 1,
          "username": "john_doe"
        },
        "related_style": null
      },
      {
        "id": 101,
        "type": "usage",
        "amount": 50,
        "currency_code": "KRW",
        "status": "completed",
        "memo": "이미지 생성 결제",
        "created_at": "2025-01-15T11:00:00Z",
        "sender": {
          "id": 1,
          "username": "john_doe"
        },
        "receiver": {
          "id": 5,
          "username": "artist_name"
        },
        "related_style": {
          "id": 10,
          "name": "Watercolor Style"
        },
        "related_generation": {
          "id": 500,
          "result_url": "https://s3.../generated_500.jpg"
        }
      }
    ],
    "next_cursor": "2025-01-15T11:00:00Z",
    "has_more": true
  }
}
```

#### 거래 타입 판별 규칙
거래 타입은 DB에 저장되지 않으며, 다음 필드 조합으로 프론트엔드에서 판별:
- `purchase` (토큰 구매): `sender` 존재, `receiver=null`, `related_generation_id=null`
- `welcome` (웰컴 보너스): `sender=null`, `receiver` 존재, `memo='Welcome Bonus'`
- `usage` (이미지 생성 결제): `sender` 존재, `receiver` 존재, `related_generation_id` 존재
- `transfer` (송금, MVP 제외): `sender` 존재, `receiver` 존재, `related_generation_id=null`

---

### 4.3 토큰 구매 시작

#### Request
```http
POST /api/tokens/purchase
Content-Type: application/json
X-CSRFToken: xyz789...

{
  "package_id": "basic_100"
}
```

**지원 패키지**:
- `basic_100`: 100 토큰, ₩10,000
- `standard_500`: 500 토큰, ₩45,000 (10% 할인)
- `premium_1000`: 1000 토큰, ₩80,000 (20% 할인)

#### Response
```json
{
  "success": true,
  "data": {
    "order_id": "ORDER_20250115_123456",
    "payment_url": "https://pay.toss.im/...",
    "package_id": "basic_100",
    "amount_tokens": 100,
    "price_per_token": 100.00,
    "currency_code": "KRW",
    "total_price": 10000.00,
    "expires_at": "2025-01-15T12:15:00Z"
  }
}
```

#### 설명
1. **클라이언트**: 패키지 ID만 전달 (가격은 서버에서 결정)
2. **Backend**:
   - 패키지 정의에서 가격 조회 (조작 불가)
   - `purchases` 레코드 생성 (`status='pending'`)
   - 토스 결제 URL 생성하여 반환
3. **프론트엔드**: `payment_url`로 리다이렉트
4. **토스 결제 완료**: Webhook 호출 → 토큰 충전

#### 에러
- `401 UNAUTHORIZED`: 로그인 필요
- `400 INVALID_PACKAGE`: 존재하지 않는 패키지 ID
- `422 VALIDATION_ERROR`: 유효하지 않은 요청

---

## 5. 스타일 API

### 5.1 스타일 목록 조회

#### Request
```http
GET /api/styles?sort=popular&cursor=...&limit=20&tags=watercolor,portrait
```

**쿼리 파라미터**:
- `sort`: `recent` (기본값), `popular`
- `tags`: 쉼표로 구분된 태그 목록 (AND 조건)
- `artist_id`: 특정 작가의 스타일만 (선택)
- `training_status`: `completed` (기본값), `all`

#### Response
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 10,
        "name": "Watercolor Dreams",
        "description": "부드러운 수채화 스타일",
        "thumbnail_url": "https://s3.../thumbnail.jpg",
        "artist": {
          "id": 5,
          "username": "artist_name",
          "artist_name": "Artist Display Name"
        },
        "training_status": "completed",
        "generation_cost_tokens": 50,
        "usage_count": 1234,
        "tags": ["watercolor", "portrait"],
        "created_at": "2025-01-01T00:00:00Z"
      }
    ],
    "next_cursor": "2025-01-01T00:00:00Z",
    "has_more": true
  }
}
```

#### 정렬 기준
- `recent`: `created_at DESC`
- `popular`: `usage_count DESC, created_at DESC`
  - usage_count = 실제 생성 횟수 (generations 테이블 COUNT)

---

### 5.2 스타일 상세 조회 (진행 상황 포함)

#### Request
```http
GET /api/styles/:id
```

#### Response (학습 완료 - 일반 사용자)
```json
{
  "success": true,
  "data": {
    "id": 10,
    "name": "Watercolor Dreams",
    "description": "부드러운 수채화 스타일...",
    "thumbnail_url": "https://s3.../thumbnail.jpg",
    "artist": {
      "id": 5,
      "username": "artist_name",
      "artist_name": "Artist Display Name",
      "profile_image": "https://s3.../profile.jpg",
      "follower_count": 123
    },
    "training_status": "completed",
    "generation_cost_tokens": 50,
    "license_type": "personal",
    "valid_from": "2025-01-01",
    "valid_to": null,
    "is_active": true,
    "created_at": "2025-01-01T00:00:00Z",
    "updated_at": "2025-01-01T02:30:00Z",
    "tags": ["watercolor", "portrait", "dreamy"],
    "stats": {
      "total_generations": 1234,
      "avg_likes": 15.5
    },
    "sample_artworks": [
      {
        "id": 100,
        "image_url": "https://s3.../artwork1.jpg",
        "tags": ["woman", "portrait"]
      }
    ],
    "progress": null
  }
}
```

#### Response (학습 완료 - 소유자/관리자)
소유자(`artist_id == request.user.id`) 또는 관리자만 `model_path` 필드 포함:
```json
{
  "success": true,
  "data": {
    "id": 10,
    "name": "Watercolor Dreams",
    "training_status": "completed",
    "model_path": "s3://bucket/models/style_10.safetensors",
    "training_metric": {
      "loss": 0.05,
      "epochs": 100
    },
    ...
  }
}
```

**보안**: `model_path`는 내부 스토리지 경로로 소유자만 조회 가능

#### Response (학습 중)
```json
{
  "success": true,
  "data": {
    "id": 10,
    "name": "My Style",
    "training_status": "training",
    "progress": {
      "current_epoch": 50,
      "total_epochs": 100,
      "progress_percent": 50,
      "estimated_seconds": 900,
      "last_updated": "2025-01-15T12:00:00Z"
    },
    "created_at": "2025-01-15T10:00:00Z"
  }
}
```

#### 진행 상황 필드 설명
- `progress`: `training_status='training'`일 때만 존재, 그 외 `null`
- `current_epoch`: 현재 에포크 (0부터 시작)
- `total_epochs`: 전체 에포크 수
- `progress_percent`: 진행률 (0-100)
- `estimated_seconds`: 예상 남은 시간 (초)
- `last_updated`: 마지막 업데이트 시각 (Training Server가 30초마다 전송)

#### 에러
- `404 NOT_FOUND`: 스타일 없음

---

### 5.3 스타일 생성 (학습 요청)

#### Request
```http
POST /api/styles
Content-Type: multipart/form-data
X-CSRFToken: xyz789...

{
  "name": "My Watercolor Style",
  "description": "부드러운 수채화 스타일",
  "generation_cost_tokens": 50,
  "license_type": "personal",
  "tags": ["watercolor", "portrait"],
  "images": [File, File, ...],  // 10~100장
  "image_tags": {
    "0": ["woman", "portrait"],
    "1": ["landscape", "mountain"]
  }
}
```

#### Validation
- **이미지 수**: 10~100장
- **파일 형식**: JPG, PNG만
- **해상도**: 최소 512×512px
- **파일 크기**: 최대 10MB/장
- **태그**: 영어만 허용
- **MVP 제한**: 작가당 1개 스타일만 생성 가능

#### Response
```json
{
  "success": true,
  "data": {
    "id": 10,
    "name": "My Watercolor Style",
    "training_status": "pending",
    "artwork_count": 15,
    "created_at": "2025-01-15T10:00:00Z",
    "progress": null
  }
}
```

#### 에러
- `403 ARTIST_ONLY`: 작가 권한 필요
- `403 STYLE_LIMIT_REACHED`: MVP 제한 (1개)
- `422 INVALID_IMAGE_FORMAT`: 지원하지 않는 형식
- `422 IMAGE_SIZE_EXCEEDED`: 파일 크기 초과
- `422 IMAGE_RESOLUTION_TOO_LOW`: 해상도 부족
- `422 INSUFFICIENT_IMAGES`: 이미지 수 부족 (10장 미만)
- `422 TOO_MANY_IMAGES`: 이미지 수 초과 (100장 초과)

---

### 5.4 스타일 메타데이터 수정

#### Request
```http
PATCH /api/styles/:id
Content-Type: application/json
X-CSRFToken: xyz789...

{
  "description": "수정된 설명",
  "generation_cost_tokens": 60,
  "is_active": true
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "id": 10,
    "description": "수정된 설명",
    "generation_cost_tokens": 60,
    "is_active": true,
    "updated_at": "2025-01-15T12:00:00Z"
  }
}
```

#### 제약
- `training_status='completed'` 상태에서만 가격/설명 수정 가능
- `name`은 수정 불가 (고유 식별자)

#### 에러
- `403 FORBIDDEN`: 소유자가 아님
- `422 STYLE_NOT_READY`: 학습 미완료

---

### 5.5 내 스타일 목록 조회

#### Request
```http
GET /api/styles/me
```

#### Response
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 10,
        "name": "My Style",
        "training_status": "completed",
        "generation_cost_tokens": 50,
        "usage_count": 123,
        "total_earned_tokens": 6150,
        "progress": null,
        "created_at": "2025-01-01T00:00:00Z"
      }
    ]
  }
}
```

#### 에러
- `403 ARTIST_ONLY`: 작가 권한 필요

---

## 6. 생성 API

### 6.1 이미지 생성 요청

#### Request
```http
POST /api/generations
Content-Type: application/json
X-CSRFToken: xyz789...

{
  "style_id": 10,
  "prompt_tags": ["woman", "portrait", "sunset"],
  "description": "노을 배경의 여성 초상화",
  "aspect_ratio": "1:1",
  "seed": 42
}
```

**파라미터**:
- `style_id` (필수): 사용할 스타일 ID
- `prompt_tags` (필수): 프롬프트 태그 배열 (영어)
- `description` (선택): 이미지 설명 (한글 가능)
- `aspect_ratio`: `1:1` (기본값), `2:2`, `1:2`
- `seed` (선택): 재현 가능한 생성을 위한 시드값

#### Response
```json
{
  "success": true,
  "data": {
    "id": 500,
    "user_id": 1,
    "style_id": 10,
    "status": "queued",
    "consumed_tokens": 50,
    "aspect_ratio": "1:1",
    "created_at": "2025-01-15T12:00:00Z",
    "progress": null
  }
}
```

#### 에러
- `402 INSUFFICIENT_TOKENS`: 토큰 부족
- `404 NOT_FOUND`: 스타일 없음
- `422 STYLE_NOT_READY`: 학습 미완료 스타일

---

### 6.2 생성 상태 조회 (진행 상황 포함)

#### Request
```http
GET /api/generations/:id
```

#### Response (대기 중)
```json
{
  "success": true,
  "data": {
    "id": 500,
    "status": "queued",
    "consumed_tokens": 50,
    "created_at": "2025-01-15T12:00:00Z",
    "progress": null
  }
}
```

#### Response (처리 중)
```json
{
  "success": true,
  "data": {
    "id": 500,
    "status": "processing",
    "consumed_tokens": 50,
    "progress": {
      "current_step": 38,
      "total_steps": 50,
      "progress_percent": 76,
      "estimated_seconds": 3,
      "last_updated": "2025-01-15T12:00:05Z"
    },
    "created_at": "2025-01-15T12:00:00Z"
  }
}
```

#### Response (완료)
```json
{
  "success": true,
  "data": {
    "id": 500,
    "user_id": 1,
    "style": {
      "id": 10,
      "name": "Watercolor Dreams",
      "artist": {
        "id": 5,
        "artist_name": "Artist Name"
      }
    },
    "status": "completed",
    "result_url": "https://s3.../generated_500.jpg",
    "description": "노을 배경의 여성 초상화",
    "aspect_ratio": "1:1",
    "is_public": false,
    "like_count": 0,
    "comment_count": 0,
    "tags": ["woman", "portrait", "sunset"],
    "consumed_tokens": 50,
    "progress": null,
    "created_at": "2025-01-15T12:00:00Z",
    "updated_at": "2025-01-15T12:00:10Z"
  }
}
```

#### Response (실패)
```json
{
  "success": true,
  "data": {
    "id": 500,
    "status": "failed",
    "error_message": "GPU memory exceeded",
    "refunded": true,
    "progress": null,
    "created_at": "2025-01-15T12:00:00Z"
  }
}
```

#### 진행 상황 필드 설명
- `progress`: `status='processing'`일 때만 존재, 그 외 `null`
- `current_step`: 현재 diffusion step
- `total_steps`: 전체 step 수 (보통 50)
- `progress_percent`: 진행률 (0-100)
- `estimated_seconds`: 예상 남은 시간
- `last_updated`: 마지막 업데이트 시각

#### 상태 코드
- `queued`: 대기 중
- `processing`: 생성 중
- `retrying`: 재시도 중 (1~3회)
- `completed`: 완료
- `failed`: 실패 (토큰 환불됨)

#### 에러
- `404 NOT_FOUND`: 생성 요청 없음

---

### 6.3 공개 피드 조회

#### Request
```http
GET /api/generations/feed?cursor=...&limit=20&tags=portrait
```

**쿼리 파라미터**:
- `tags`: 태그 필터 (쉼표 구분)
- `sort`: `recent` (기본값), `popular`

#### Response
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 500,
        "user": {
          "id": 1,
          "username": "john_doe",
          "profile_image": "https://s3.../profile.jpg"
        },
        "style": {
          "id": 10,
          "name": "Watercolor Dreams"
        },
        "result_url": "https://s3.../generated_500.jpg",
        "description": "노을 배경의 여성 초상화",
        "like_count": 15,
        "comment_count": 3,
        "is_liked": false,
        "tags": ["woman", "portrait", "sunset"],
        "created_at": "2025-01-15T12:00:00Z"
      }
    ],
    "next_cursor": "2025-01-15T12:00:00Z",
    "has_more": true
  }
}
```

#### 정렬 기준
- `recent`: `created_at DESC`
- `popular`: `like_count DESC, created_at DESC`

#### 설명
- `is_liked`: 로그인한 사용자가 좋아요 누른 경우 `true`
- `is_public=true`인 이미지만 노출

---

### 6.4 내 생성 이미지 목록

#### Request
```http
GET /api/generations/me?cursor=...&limit=20&status=completed
```

**쿼리 파라미터**:
- `status`: `all` (기본값), `completed`, `failed`, `processing`
- `is_public`: `all` (기본값), `true`, `false`

#### Response
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 500,
        "style": {
          "id": 10,
          "name": "Watercolor Dreams"
        },
        "result_url": "https://s3.../generated_500.jpg",
        "status": "completed",
        "is_public": false,
        "like_count": 15,
        "consumed_tokens": 50,
        "progress": null,
        "created_at": "2025-01-15T12:00:00Z"
      }
    ],
    "next_cursor": "2025-01-15T12:00:00Z",
    "has_more": true
  }
}
```

---

### 6.5 생성 이미지 수정

#### Request
```http
PATCH /api/generations/:id
Content-Type: application/json
X-CSRFToken: xyz789...

{
  "is_public": true,
  "description": "수정된 설명"
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "id": 500,
    "is_public": true,
    "description": "수정된 설명",
    "updated_at": "2025-01-15T12:30:00Z"
  }
}
```

#### 에러
- `403 FORBIDDEN`: 소유자가 아님

#### MVP 제한
- 이미지 삭제 불가
- 비공개 전환(`is_public=false`)으로 숨김 처리

---

## 7. 커뮤니티 API

### 7.1 팔로우/언팔로우

#### 팔로우
```http
POST /api/users/:id/follow
X-CSRFToken: xyz789...
```

**Response**:
```json
{
  "success": true,
  "data": {
    "following": true,
    "follower_count": 124
  }
}
```

#### 언팔로우
```http
DELETE /api/users/:id/follow
X-CSRFToken: xyz789...
```

**Response**:
```json
{
  "success": true,
  "data": {
    "following": false,
    "follower_count": 123
  }
}
```

#### 에러
- `400 SELF_FOLLOW_NOT_ALLOWED`: 자기 자신 팔로우 불가
- `409 DUPLICATE_FOLLOW`: 이미 팔로우 중

---

### 7.2 팔로잉 목록 조회

#### Request
```http
GET /api/users/me/following?cursor=...&limit=20
```

#### Response
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 3,
        "username": "artist1",
        "profile_image": "https://s3.../profile.jpg",
        "artist_name": "Artist One",
        "role": "artist",
        "follower_count": 456,
        "followed_at": "2025-01-05T00:00:00Z"
      }
    ],
    "next_cursor": "2025-01-05T00:00:00Z",
    "has_more": true
  }
}
```

#### MVP 제한
- 팔로워 목록 조회 불가 (내가 팔로잉하는 목록만)
- 타인의 팔로잉 목록도 조회 불가

---

### 7.3 좋아요/좋아요 취소

#### 좋아요
```http
POST /api/generations/:id/like
X-CSRFToken: xyz789...
```

**Response**:
```json
{
  "success": true,
  "data": {
    "liked": true,
    "like_count": 16
  }
}
```

#### 좋아요 취소
```http
DELETE /api/generations/:id/like
X-CSRFToken: xyz789...
```

**Response**:
```json
{
  "success": true,
  "data": {
    "liked": false,
    "like_count": 15
  }
}
```

#### 에러
- `409 DUPLICATE_LIKE`: 이미 좋아요 누름

---

### 7.4 댓글 목록 조회

#### Request
```http
GET /api/generations/:id/comments?cursor=...&limit=20
```

#### Response
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 100,
        "user": {
          "id": 2,
          "username": "commenter",
          "profile_image": "https://s3.../profile.jpg"
        },
        "content": "정말 멋진 작품이에요!",
        "like_count": 5,
        "parent_id": null,
        "replies": [
          {
            "id": 101,
            "user": {
              "id": 1,
              "username": "john_doe"
            },
            "content": "감사합니다!",
            "parent_id": 100,
            "created_at": "2025-01-15T12:15:00Z"
          }
        ],
        "created_at": "2025-01-15T12:10:00Z",
        "updated_at": "2025-01-15T12:10:00Z"
      }
    ],
    "next_cursor": "2025-01-15T12:10:00Z",
    "has_more": true
  }
}
```

#### 설명
- `parent_id=null`: 일반 댓글
- `parent_id!=null`: 대댓글
- MVP: 1단계 대댓글만 (대댓글의 대댓글 불가)

---

### 7.5 댓글 작성

#### Request
```http
POST /api/generations/:id/comments
Content-Type: application/json
X-CSRFToken: xyz789...

{
  "content": "정말 멋진 작품이에요!",
  "parent_id": null
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "id": 100,
    "user": {
      "id": 1,
      "username": "john_doe"
    },
    "content": "정말 멋진 작품이에요!",
    "parent_id": null,
    "created_at": "2025-01-15T12:10:00Z"
  }
}
```

#### 에러
- `422 REPLY_DEPTH_EXCEEDED`: 대댓글의 대댓글 시도 (MVP 제한)

---

### 7.6 댓글 수정

#### Request
```http
PATCH /api/comments/:id
Content-Type: application/json
X-CSRFToken: xyz789...

{
  "content": "수정된 댓글"
}
```

#### Response
```json
{
  "success": true,
  "data": {
    "id": 100,
    "content": "수정된 댓글",
    "updated_at": "2025-01-15T12:20:00Z"
  }
}
```

#### 에러
- `403 FORBIDDEN`: 작성자가 아님

---

### 7.7 댓글 삭제

#### Request
```http
DELETE /api/comments/:id
X-CSRFToken: xyz789...
```

#### Response
```json
{
  "success": true,
  "message": "댓글이 삭제되었습니다"
}
```

#### 설명
- 댓글 삭제 시 대댓글도 CASCADE 삭제
- 작성자 본인 또는 관리자만 삭제 가능

---

## 8. 검색 API

### 8.1 통합 검색

#### Request
```http
GET /api/search?q=watercolor&type=all&limit=20
```

**쿼리 파라미터**:
- `q` (필수): 검색어
- `type`: `all` (기본값), `styles`, `artists`
- `limit`: 결과 수 (1-100, 기본값 20)

#### Response
```json
{
  "success": true,
  "data": {
    "styles": [
      {
        "id": 10,
        "name": "Watercolor Dreams",
        "thumbnail_url": "https://s3.../thumbnail.jpg",
        "artist": {
          "id": 5,
          "artist_name": "John Artist"
        },
        "matched_by": "tag",
        "usage_count": 1234
      }
    ],
    "artists": [
      {
        "id": 5,
        "username": "watercolor_master",
        "artist_name": "Watercolor Master",
        "profile_image": "https://s3.../profile.jpg",
        "follower_count": 1234,
        "matched_by": "name"
      }
    ]
  }
}
```

#### 검색 로직
- **스타일 검색**:
  - 태그 매칭 (`tags.name LIKE '%watercolor%'`)
  - 스타일 이름 매칭 (`styles.name LIKE '%watercolor%'`)
  - 스타일 이름은 자동으로 태그에 포함됨
  
- **작가 검색**:
  - 작가명 매칭 (`artists.artist_name LIKE '%watercolor%'`)
  - 유저명 매칭 (`users.username LIKE '%watercolor%'`)

#### type 파라미터 사용
```
GET /api/search?q=watercolor&type=styles  # 스타일만
GET /api/search?q=watercolor&type=artists # 작가만
GET /api/search?q=watercolor&type=all     # 통합 (기본값)
```

#### MVP 제외 기능
- 인기 태그 API (`/api/tags/popular`)
- 태그 자동완성 API (`/api/tags/autocomplete`)

---

## 9. 알림 API

### 9.1 알림 목록 조회

#### Request
```http
GET /api/notifications?cursor=...&limit=20&unread_only=false
```

**쿼리 파라미터**:
- `unread_only`: `true` (읽지 않은 것만), `false` (기본값, 전체)

#### Response
```json
{
  "success": true,
  "data": {
    "results": [
      {
        "id": 1000,
        "type": "like",
        "actor": {
          "id": 2,
          "username": "user2",
          "profile_image": "https://s3.../profile.jpg"
        },
        "target_type": "generation",
        "target_id": 500,
        "target": {
          "id": 500,
          "result_url": "https://s3.../generated_500.jpg"
        },
        "is_read": false,
        "created_at": "2025-01-15T12:00:00Z"
      },
      {
        "id": 1001,
        "type": "generation_complete",
        "actor": null,
        "target_type": "generation",
        "target_id": 501,
        "is_read": true,
        "created_at": "2025-01-15T11:00:00Z"
      }
    ],
    "next_cursor": "2025-01-15T11:00:00Z",
    "has_more": true,
    "unread_count": 5
  }
}
```

#### 알림 타입
- `follow`: 팔로우 알림 (`actor` 존재)
- `like`: 좋아요 알림 (`actor` 존재)
- `comment`: 댓글 알림 (`actor` 존재)
- `generation_complete`: 생성 완료 (시스템, `actor=null`)
- `generation_failed`: 생성 실패 (시스템, `actor=null`)
- `style_training_complete`: 학습 완료 (시스템, `actor=null`)
- `style_training_failed`: 학습 실패 (시스템, `actor=null`)

---

### 9.2 알림 읽음 처리

#### Request
```http
PATCH /api/notifications/:id/read
X-CSRFToken: xyz789...
```

#### Response
```json
{
  "success": true,
  "data": {
    "id": 1000,
    "is_read": true
  }
}
```

---

### 9.3 모든 알림 읽음 처리

#### Request
```http
POST /api/notifications/read-all
X-CSRFToken: xyz789...
```

#### Response
```json
{
  "success": true,
  "message": "모든 알림이 읽음 처리되었습니다",
  "data": {
    "updated_count": 5
  }
}
```

---

## 10. Webhook API

**⚠️ 내부 서버 간 통신 전용, 외부 접근 차단**

### 10.1 인증 방식

#### Request Header
```http
Authorization: Bearer <INTERNAL_API_TOKEN>
X-Request-Source: training-server | inference-server
```

#### 보안 설정
- 환경변수: `INTERNAL_API_TOKEN` (긴 UUID, 최소 32자)
- IP 화이트리스트: AI 서버 IP만 허용
- 토큰 Rotation: 월 1회
- 요청 검증 실패 시 401 반환

---

### 10.2 토스 결제 Webhook

#### Request
```http
POST /api/webhooks/toss/payment
Content-Type: application/json

{
  "paymentKey": "payment_key_123",
  "orderId": "ORDER_20250115_123456",
  "status": "DONE",
  "totalAmount": 10000,
  "approvedAt": "2025-01-15T12:00:00+09:00"
}
```

#### Response
```http
200 OK
{
  "success": true
}
```

#### 처리 로직
1. `paymentKey`로 멱등성 검증 (중복 처리 방지)
2. `purchases.status` 업데이트: `pending` → `paid`
3. `users.token_balance` 증가
4. `transactions` 레코드 생성

---

### 10.3 스타일 학습 완료

#### Request
```http
POST /api/webhooks/training/complete
Authorization: Bearer <INTERNAL_API_TOKEN>
X-Request-Source: training-server
Content-Type: application/json

{
  "style_id": 10,
  "model_path": "s3://bucket/models/style_10.safetensors",
  "training_metric": {
    "loss": 0.05,
    "epochs": 100
  }
}
```

#### Response
```http
200 OK
{
  "success": true
}
```

#### 처리 로직
1. `styles.training_status` 업데이트: `training` → `completed`
2. `styles.model_path` 저장
3. `styles.training_metric` 저장
4. `styles.progress` = `null`
5. 작가에게 알림 전송 (`style_training_complete`)

---

### 10.4 스타일 학습 실패

#### Request
```http
POST /api/webhooks/training/failed
Authorization: Bearer <INTERNAL_API_TOKEN>
X-Request-Source: training-server
Content-Type: application/json

{
  "style_id": 10,
  "error_message": "Insufficient training data quality",
  "error_code": "LOW_QUALITY_DATA"
}
```

#### Response
```http
200 OK
{
  "success": true
}
```

#### 처리 로직
1. `styles.training_status` 업데이트: `training` → `failed`
2. `styles.progress` = `null`
3. 작가에게 에러 알림 전송 (`style_training_failed`)

---

### 10.5 이미지 생성 완료

#### Request
```http
POST /api/webhooks/inference/complete
Authorization: Bearer <INTERNAL_API_TOKEN>
X-Request-Source: inference-server
Content-Type: application/json

{
  "generation_id": 500,
  "result_url": "https://s3.../generated_500.jpg",
  "metadata": {
    "seed": 42,
    "steps": 50,
    "guidance_scale": 7.5
  }
}
```

#### Response
```http
200 OK
{
  "success": true
}
```

#### 처리 로직
1. `generations.status` 업데이트: `processing` → `completed`
2. `generations.result_url` 저장
3. `generations.progress` = `null`
4. 사용자에게 알림 전송 (`generation_complete`)

---

### 10.6 이미지 생성 실패

#### Request
```http
POST /api/webhooks/inference/failed
Authorization: Bearer <INTERNAL_API_TOKEN>
X-Request-Source: inference-server
Content-Type: application/json

{
  "generation_id": 500,
  "error_message": "GPU out of memory",
  "error_code": "GPU_OOM",
  "retry_count": 3
}
```

#### Response
```http
200 OK
{
  "success": true
}
```

#### 처리 로직
1. **재시도 판단**:
   - `retry_count < 3` + 재시도 가능 오류 → `status='retrying'` + 재시도 큐 전송
   - 그 외 → `status='failed'` + 토큰 환불

2. **최종 실패 시**:
   - `generations.status` = `failed`
   - `generations.progress` = `null`
   - 토큰 환불 (원자적 트랜잭션)
   - 사용자에게 에러 알림 전송 (`generation_failed`)

---

### 10.7 진행 상황 업데이트

#### 스타일 학습 진행
```http
PATCH /api/styles/:id
Authorization: Bearer <INTERNAL_API_TOKEN>
X-Request-Source: training-server
Content-Type: application/json

{
  "progress": {
    "current_epoch": 50,
    "total_epochs": 100,
    "progress_percent": 50,
    "estimated_seconds": 900
  }
}
```

#### 이미지 생성 진행
```http
PATCH /api/generations/:id
Authorization: Bearer <INTERNAL_API_TOKEN>
X-Request-Source: inference-server
Content-Type: application/json

{
  "progress": {
    "current_step": 38,
    "total_steps": 50,
    "progress_percent": 76,
    "estimated_seconds": 3
  }
}
```

#### Response
```http
200 OK
{
  "success": true
}
```

#### 설명
- Training Server: 30초마다 전송
- Inference Server: 주요 단계(10%, 25%, 50%, 75%, 90%)마다 전송
- `progress` JSONB 필드에 저장
- 프론트엔드는 5초마다 폴링하여 최대 30초 지연

---

## 11. 에러 코드

### 11.1 HTTP 상태 코드

| 코드 | 의미 | 사용 예시 |
|------|------|----------|
| **200** | OK | 성공 |
| **201** | Created | 리소스 생성 성공 |
| **400** | Bad Request | 잘못된 요청 파라미터 |
| **401** | Unauthorized | 인증 필요 (로그인 안 함) |
| **402** | Payment Required | 토큰 부족 |
| **403** | Forbidden | 권한 없음 |
| **404** | Not Found | 리소스 없음 |
| **409** | Conflict | 리소스 충돌 |
| **422** | Unprocessable Entity | 유효성 검증 실패 |
| **429** | Too Many Requests | Rate Limit 초과 |
| **500** | Internal Server Error | 서버 내부 오류 |

---

### 11.2 애플리케이션 에러 코드

#### 인증 & 권한
- `UNAUTHORIZED` (401): 로그인 필요
- `FORBIDDEN` (403): 접근 권한 없음
- `ARTIST_ONLY` (403): 작가 권한 필요
- `SESSION_EXPIRED` (401): 세션 만료

#### 토큰 관련
- `INSUFFICIENT_TOKENS` (402): 토큰 잔액 부족
- `PAYMENT_FAILED` (402): 결제 실패
- `INVALID_TOKEN_AMOUNT` (400): 유효하지 않은 토큰 수량
- `PURCHASE_EXPIRED` (400): 결제 만료

#### 스타일 관련
- `STYLE_LIMIT_REACHED` (403): 스타일 생성 한도 초과 (MVP: 1개)
- `STYLE_NOT_FOUND` (404): 스타일 없음
- `STYLE_NOT_READY` (422): 학습 미완료 스타일
- `TRAINING_IN_PROGRESS` (409): 이미 학습 진행 중
- `TRAINING_FAILED` (500): 모델 학습 실패

#### 이미지 업로드
- `INVALID_IMAGE_FORMAT` (422): 지원하지 않는 형식 (JPG, PNG만)
- `IMAGE_SIZE_EXCEEDED` (422): 파일 크기 초과 (10MB)
- `IMAGE_RESOLUTION_TOO_LOW` (422): 해상도 부족 (최소 512×512)
- `INSUFFICIENT_IMAGES` (422): 이미지 수 부족 (최소 10장)
- `TOO_MANY_IMAGES` (422): 이미지 수 초과 (최대 100장)

#### 이미지 생성
- `GENERATION_FAILED` (500): 이미지 생성 실패
- `GENERATION_NOT_FOUND` (404): 생성 요청 없음
- `GENERATION_STILL_PROCESSING` (409): 아직 처리 중

#### 커뮤니티
- `DUPLICATE_FOLLOW` (409): 이미 팔로우 중
- `SELF_FOLLOW_NOT_ALLOWED` (400): 자기 자신 팔로우 불가
- `DUPLICATE_LIKE` (409): 이미 좋아요함
- `COMMENT_NOT_FOUND` (404): 댓글 없음
- `REPLY_DEPTH_EXCEEDED` (422): 대댓글 깊이 초과 (MVP: 1단계)

#### 태그
- `TAG_NOT_FOUND` (404): 태그 없음
- `INVALID_TAG_LANGUAGE` (422): 영어가 아닌 태그

#### 기타
- `RATE_LIMIT_EXCEEDED` (429): 요청 횟수 초과
- `RESOURCE_NOT_FOUND` (404): 일반 리소스 없음
- `VALIDATION_ERROR` (422): 입력 검증 실패
- `INTERNAL_SERVER_ERROR` (500): 서버 내부 오류

---

## 12. Rate Limiting

### 12.1 제한 정책

| 엔드포인트 유형 | 제한 | 식별 기준 | 리셋 방식 |
|--------------|------|----------|----------|
| 로그인 시도 | 5회 / 5분 | IP | 슬라이딩 윈도우 |
| 이미지 생성 | 6회 / 분 | User ID | 슬라이딩 윈도우 |
| 인증 필요 API | 100회 / 분 | User ID | 슬라이딩 윈도우 |
| 비인증 API | 50회 / 분 | IP | 슬라이딩 윈도우 |

### 12.2 초과 시 처리

#### Response
```http
429 Too Many Requests
Retry-After: 45
Content-Type: application/json

{
  "success": false,
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "요청 횟수를 초과했습니다",
    "details": {
      "limit": 100,
      "window": "1 minute",
      "retry_after": 45
    }
  }
}
```

#### Headers
- `X-RateLimit-Limit`: 전체 제한 수
- `X-RateLimit-Remaining`: 남은 요청 수
- `X-RateLimit-Reset`: 리셋 시각 (Unix timestamp)
- `Retry-After`: 재시도 가능까지 남은 시간 (초)

### 12.3 구현 방식
- 라이브러리: `django-ratelimit`
- 저장소: Redis (캐시)
- 알고리즘: 슬라이딩 윈도우

### 12.4 이미지 생성 제한 근거
- 6회/분 = GPU 처리 속도 고려 (평균 10초/장)
- 동시 요청 제한으로 GPU 큐 과부하 방지
- 토큰 고갈 전에 Rate Limit 걸림

---

## 참조 문서

### 관련 문서
- **데이터베이스 스키마**: [docs/database/README.md](database/README.md)
- **쿼리 예제**: [docs/database/guides/QUERIES.md](database/guides/QUERIES.md)
- **보안 정책**: [docs/SECURITY.md](SECURITY.md)
- **배포 가이드**: [docs/DEPLOYMENT.md](DEPLOYMENT.md)

### 프로젝트 문서
- **기술 명세**: [TECHSPEC.md](../TECHSPEC.md)
- **개발 계획**: [PLAN.md](../PLAN.md)
- **Claude 가이드**: [CLAUDE.md](../CLAUDE.md)

---

**문서 버전**: 2.0  
**작성일**: 2025-10-29  
**작성자**: Development Team