# Postman API 테스트 가이드

Backend API를 Postman으로 테스트하기 위한 가이드입니다.

## 서버 정보

- **Base URL**: `http://localhost:8000`
- **API Base URL**: `http://localhost:8000/api`

## 인증 방식

**이 프로젝트는 Google OAuth 전용입니다.**
- ❌ Email/Password 로그인 **없음**
- ✅ Google OAuth **전용**

### Postman에서 API 테스트하는 방법

Google OAuth는 브라우저 기반이므로 Postman에서 직접 로그인할 수 없습니다.
다음 두 가지 방법 중 하나를 선택하세요:

#### 방법 1: 브라우저에서 세션 쿠키 복사 (권장)

1. **Frontend 서버 시작**
   ```bash
   cd apps/frontend
   npm run dev
   ```

2. **브라우저에서 로그인**
   - `http://localhost:5173` 접속
   - Google OAuth로 로그인
   - 개발자 도구 (F12) → Application → Cookies
   - `sessionid` 쿠키 값 복사

3. **Postman에서 세션 쿠키 사용**
   - Headers 탭에서 추가:
     ```
     Cookie: sessionid=<복사한-세션-값>
     ```

#### 방법 2: Django Admin에서 수동 세션 생성

1. **Superuser 생성 (최초 1회)**
   ```bash
   cd apps/backend
   python manage.py createsuperuser
   # Username: admin
   # Email: admin@example.com
   # (Password는 사용하지 않지만 입력 필요)
   ```

2. **Django Admin 접속**
   - `http://localhost:8000/admin` 접속
   - Google OAuth로 로그인 (또는 직접 세션 생성)

3. **Sessions 테이블에서 세션 생성**
   - Django Admin → Sessions → Add session
   - Session key 복사하여 Postman에서 사용

---

## 테스트 데이터

테스트 데이터는 Google OAuth 시뮬레이션으로 생성되었습니다.

### Artist 계정
- **Email**: `artist@example.com`
- **Provider**: Google
- **Provider User ID**: `google-artist-12345`
- **Role**: artist
- **Token Balance**: 1000

### User 계정
- **Email**: `user@example.com`
- **Provider**: Google
- **Provider User ID**: `google-user-67890`
- **Role**: user
- **Token Balance**: 500

---

## 1. Health Check (인증 불필요)

서버가 정상 작동하는지 확인합니다.

**Request:**
```
GET http://localhost:8000/api/health
```

**Expected Response (200 OK):**
```json
{
  "status": "healthy",
  "timestamp": "2025-11-12T08:52:00.000Z",
  "database": "connected",
  "rabbitmq": "connected"
}
```

---

## 2. 인증 API

### 2.1 현재 사용자 정보 조회

로그인된 사용자 정보를 확인합니다.

**Request:**
```
GET http://localhost:8000/api/auth/me
Cookie: sessionid=<your-session-id>
```

**Expected Response (200 OK):**
```json
{
  "id": 1,
  "username": "test_artist",
  "email": "artist@example.com",
  "provider": "google",
  "profile_image": null,
  "role": "artist",
  "token_balance": 1000,
  "bio": "Test artist account for development",
  "is_active": true,
  "created_at": "2025-11-12T04:10:00.000000Z",
  "artist_profile": {
    "artist_name": "Test Artist",
    "signature_image_url": null,
    "earned_token_balance": 0,
    "follower_count": 0
  }
}
```

**Error Response (401 Unauthorized):**
```json
{
  "error": "Not authenticated"
}
```

### 2.2 로그아웃

세션을 종료합니다.

**Request:**
```
POST http://localhost:8000/api/auth/logout
Cookie: sessionid=<your-session-id>
```

**Expected Response (200 OK):**
```json
{
  "message": "Logged out successfully"
}
```

---

## 3. Style (스타일) API

### 3.1 스타일 목록 조회

**Request:**
```
GET http://localhost:8000/api/models
```

**Query Parameters (Optional):**
- `is_active`: true/false (기본: true)
- `training_status`: pending/training/completed/failed

**Expected Response (200 OK):**
```json
{
  "results": [
    {
      "id": 1,
      "artist_id": 1,
      "artist_name": "test_artist",
      "name": "Watercolor Dreams",
      "description": "Soft watercolor painting style",
      "thumbnail_url": null,
      "training_status": "completed",
      "license_type": "personal",
      "generation_cost_tokens": 10,
      "usage_count": 0,
      "created_at": "2025-11-12T04:10:00.000000Z"
    }
  ]
}
```

### 3.2 특정 스타일 조회

**Request:**
```
GET http://localhost:8000/api/models/{style_id}
```

**Expected Response (200 OK):**
```json
{
  "id": 1,
  "artist_id": 1,
  "artist_name": "test_artist",
  "name": "Watercolor Dreams",
  "description": "Soft watercolor painting style",
  "thumbnail_url": null,
  "model_path": null,
  "training_status": "completed",
  "training_progress": null,
  "license_type": "personal",
  "valid_from": "2025-11-12",
  "valid_to": null,
  "generation_cost_tokens": 10,
  "usage_count": 0,
  "is_active": true,
  "created_at": "2025-11-12T04:10:00.000000Z"
}
```

### 3.3 스타일 생성 (Artist only)

**Request:**
```
POST http://localhost:8000/api/models
Cookie: sessionid=<artist-session-id>
Content-Type: application/json

{
  "name": "My New Style",
  "description": "Description of the style",
  "license_type": "personal",
  "generation_cost_tokens": 20
}
```

**Expected Response (201 Created):**
```json
{
  "id": 3,
  "name": "My New Style",
  "training_status": "pending",
  "message": "Style created successfully"
}
```

---

## 4. Token (토큰) API

### 4.1 내 토큰 잔액 조회

**Request:**
```
GET http://localhost:8000/api/tokens/balance
Cookie: sessionid=<your-session-id>
```

**Expected Response (200 OK):**
```json
{
  "user_id": 1,
  "username": "test_artist",
  "token_balance": 1000
}
```

### 4.2 토큰 거래 내역 조회

**Request:**
```
GET http://localhost:8000/api/tokens/transactions
Cookie: sessionid=<your-session-id>
```

**Query Parameters (Optional):**
- `transaction_type`: purchase/generation/withdrawal/transfer
- `limit`: 10 (기본: 20)

**Expected Response (200 OK):**
```json
{
  "results": [
    {
      "id": 1,
      "sender_id": null,
      "receiver_id": 1,
      "amount": 100,
      "transaction_type": "purchase",
      "status": "completed",
      "memo": "Welcome bonus for new user",
      "created_at": "2025-11-12T04:10:00.000000Z"
    }
  ]
}
```

---

## 5. Tag (태그) API

### 5.1 태그 목록 조회

**Request:**
```
GET http://localhost:8000/api/tags
```

**Expected Response (200 OK):**
```json
{
  "results": [
    {
      "id": 1,
      "name": "portrait",
      "usage_count": 0,
      "is_active": true
    },
    {
      "id": 2,
      "name": "landscape",
      "usage_count": 0,
      "is_active": true
    }
  ]
}
```

### 5.2 태그 검색

**Request:**
```
GET http://localhost:8000/api/tags?search=port
```

**Expected Response (200 OK):**
```json
{
  "results": [
    {
      "id": 1,
      "name": "portrait",
      "usage_count": 0,
      "is_active": true
    }
  ]
}
```

---

## 6. Postman Collection 설정

### 환경 변수 설정 (Environment)

Postman에서 Environment를 생성하고 다음 변수를 설정하세요:

```
base_url: http://localhost:8000
api_url: http://localhost:8000/api
session_id: <브라우저에서-복사한-세션ID>
```

### Headers 프리셋 설정

모든 인증 필요 요청에 다음 헤더 추가:

```
Cookie: sessionid={{session_id}}
Content-Type: application/json
```

---

## 7. 에러 응답

### 401 Unauthorized
```json
{
  "error": "Not authenticated"
}
```

### 403 Forbidden
```json
{
  "error": "Permission denied"
}
```

### 404 Not Found
```json
{
  "error": "Resource not found"
}
```

### 500 Internal Server Error
```json
{
  "error": "Internal server error",
  "detail": "Error message"
}
```

---

## 추가 참고사항

1. **세션 만료**: 세션은 2주 후 자동 만료됩니다 (SESSION_COOKIE_AGE=1209600)

2. **CORS**: Frontend (localhost:5173)에서만 접근 가능합니다

3. **CSRF**: API 엔드포인트는 CSRF exempt 처리되어 있습니다

4. **Google OAuth 설정**:
   - `.env` 파일에 GOOGLE_CLIENT_ID, GOOGLE_CLIENT_SECRET 필요
   - Django Admin에서 SocialApp 등록 완료됨

5. **테스트 데이터 재생성**:
   ```bash
   cd apps/backend
   python create_test_data.py
   ```
