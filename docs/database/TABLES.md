# TABLES.md

모든 테이블 정의 (CREATE TABLE, 컬럼, 제약조건, 인덱스)

[← 돌아가기](README.md)

---

## 목차
- [auth](#auth-스키마) - users, artists
- [token](#token-스키마) - transactions, purchases
- [style](#style-스키마) - styles, artworks
- [generation](#generation-스키마) - generations
- [community](#community-스키마) - follows, likes, comments
- [tagging](#tagging-스키마) - tags, style_tags, artwork_tags, generation_tags
- [system](#system-스키마) - notifications

---

## auth 스키마

### users

```sql
CREATE TABLE users (
    id                  BIGSERIAL PRIMARY KEY,
    username            VARCHAR(50) UNIQUE NOT NULL,
    provider            VARCHAR(30) DEFAULT 'google' NOT NULL,
    provider_user_id    VARCHAR(255) NOT NULL,
    profile_image       TEXT,
    role                VARCHAR(20) DEFAULT 'user' NOT NULL,
    token_balance       BIGINT DEFAULT 0 NOT NULL CHECK (token_balance >= 0),
    bio                 TEXT,
    is_active           BOOLEAN DEFAULT TRUE NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,

    CONSTRAINT unique_provider_user UNIQUE (provider, provider_user_id)
);

-- 인덱스
CREATE INDEX idx_users_provider_userid ON users(provider, provider_user_id);
CREATE INDEX idx_users_role ON users(role) WHERE role = 'artist';
```

**주요 컬럼**:
- `token_balance`: 보유 토큰 수 (음수 불가, SELECT FOR UPDATE 필수)
- `role`: 'user' 또는 'artist'
- `provider`: OAuth 제공자 (현재: 'google')
- `is_active`: 계정 활성화 상태 (탈퇴 시 false, 소프트 삭제)

**비즈니스 규칙**:
- OAuth 인증 전용 (provider + provider_user_id 조합으로 유니크)
- 토큰 차감/증가 시 트랜잭션 필수
- 작가가 스타일 사용 내역이 있으면 물리 삭제 불가 → `is_active=false`로 비활성화

---

### artists

```sql
CREATE TABLE artists (
    id                      BIGSERIAL PRIMARY KEY,
    user_id                 BIGINT NOT NULL UNIQUE 
                            REFERENCES users(id) ON DELETE CASCADE,
    artist_name             VARCHAR(100),
    signature_image_url     TEXT,
    verified_email          VARCHAR(255),
    earned_token_balance    BIGINT DEFAULT 0 NOT NULL 
                            CHECK (earned_token_balance >= 0),
    follower_count          INT DEFAULT 0 NOT NULL,
    created_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 인덱스
CREATE INDEX idx_artists_user_id ON artists(user_id);
```

**주요 컬럼**:
- `user_id`: users.id와 1:1 관계
- `earned_token_balance`: 수익 잔액 (미정산)
- `follower_count`: 팔로우 수 캐싱용
- `signature_image_url`: 생성 이미지 워터마크용

**비즈니스 규칙**:
- 사용자가 작가 권한 획득 시 생성
- 수익 정산 시 earned_token_balance 차감

---

## token 스키마

### transactions

```sql
CREATE TABLE transactions (
    id                      BIGSERIAL PRIMARY KEY,
    sender_id               BIGINT NOT NULL
                            REFERENCES users(id) ON DELETE CASCADE,
    receiver_id             BIGINT
                            REFERENCES users(id) ON DELETE CASCADE,
    amount                  BIGINT NOT NULL,
    price_per_token         DECIMAL(10,2),
    currency_code           CHAR(3) DEFAULT 'KRW',
    total_price             DECIMAL(18,2) GENERATED ALWAYS AS
                            (amount * price_per_token) STORED,
    status                  VARCHAR(20) DEFAULT 'completed' NOT NULL
                            CHECK (status IN ('pending','completed','failed')),
    memo                    TEXT,
    created_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    related_style_id        BIGINT REFERENCES styles(id) ON DELETE SET NULL,
    related_generation_id   BIGINT REFERENCES generations(id) ON DELETE SET NULL,
    payment_method          VARCHAR(30) DEFAULT 'token' NOT NULL,
    refunded                BOOLEAN DEFAULT FALSE NOT NULL
);

-- 인덱스
CREATE INDEX idx_transactions_sender ON transactions(sender_id, created_at DESC);
CREATE INDEX idx_transactions_receiver ON transactions(receiver_id, created_at DESC);
CREATE INDEX idx_transactions_style ON transactions(related_style_id);
CREATE INDEX idx_transactions_generation ON transactions(related_generation_id);
CREATE INDEX idx_transactions_status ON transactions(status, created_at DESC);
```

**주요 컬럼**:
- `sender_id`: 토큰 차감 대상
- `receiver_id`: 토큰 증가 대상 (NULL = 플랫폼으로부터 구매)
- `currency_code`: 통화 코드 (기본값: 'KRW')
- `related_style_id`: 이미지 생성 결제 시 사용한 스타일
- `related_generation_id`: 이미지 생성 결제 시 생성된 이미지 ID
- `refunded`: 환불 여부 (true면 잔액 계산 제외)

**거래 유형 판별**:
- `receiver_id=NULL`: 토큰 구매 (플랫폼에서 지급)
- `receiver_id!=NULL, related_generation_id=NULL`: 송금 또는 웰컴 보너스
- `receiver_id!=NULL, related_generation_id!=NULL`: 이미지 생성 결제

**비즈니스 규칙**:
- **토큰 잔액 관리**: `users.token_balance`가 단일 진실 공급원(Single Source of Truth)
- **transactions 테이블 역할**: 이벤트 로그 및 감사 추적(audit trail)용
- 거래 생성 시 `users.token_balance`를 애플리케이션에서 직접 업데이트 (atomic)
- transactions는 이력 기록만, 잔액 계산에 직접 사용하지 않음

---

### purchases

```sql
CREATE TABLE purchases (
    id                          BIGSERIAL PRIMARY KEY,
    buyer_id                    BIGINT NOT NULL 
                                REFERENCES users(id) ON DELETE CASCADE,
    amount_tokens               BIGINT NOT NULL CHECK (amount_tokens > 0),
    price_per_token             DECIMAL(18,4) NOT NULL,
    currency_code               CHAR(3) NOT NULL DEFAULT 'KRW',
    total_price                 DECIMAL(18,2) GENERATED ALWAYS AS 
                                (amount_tokens * price_per_token) STORED,
    provider                    VARCHAR(30) NOT NULL DEFAULT 'toss',
    provider_payment_key        VARCHAR(120) UNIQUE NOT NULL,
    provider_order_id           VARCHAR(120) NOT NULL,
    status                      VARCHAR(20) NOT NULL DEFAULT 'pending' 
                                CHECK (status IN ('pending','authorized','paid','failed')),
    approved_at                 TIMESTAMPTZ,
    created_at                  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at                  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    -- 토스 상세 정보 (생략 가능)
    provider_total_amount       DECIMAL(18,2),
    receipt_url                 TEXT,
    card_detail                 JSONB,
    easy_pay_detail             JSONB,
    memo                        TEXT
);

-- 인덱스
CREATE INDEX idx_purchases_buyer ON purchases(buyer_id, created_at DESC);
CREATE INDEX idx_purchases_status ON purchases(status);
CREATE INDEX idx_purchases_order_id ON purchases(provider_order_id);
```

**주요 컬럼**:
- `provider_payment_key`: 토스 고유 식별자 (멱등성 보장)
- `status`: pending → paid (웹훅에서 업데이트)
- `card_detail`: 결제 수단 원본 데이터 (JSONB)

**비즈니스 규칙**:
- 웹훅 수신 시 payment_key로 중복 확인
- status='paid'일 때만 토큰 충전

---

## style 스키마

### styles

```sql
CREATE TABLE styles (
    id                      BIGSERIAL PRIMARY KEY,
    artist_id               BIGINT NOT NULL 
                            REFERENCES users(id) ON DELETE CASCADE,
    name                    VARCHAR(100) NOT NULL,
    description             TEXT,
    thumbnail_url           TEXT,
    model_path              TEXT,
    training_status         VARCHAR(20) DEFAULT 'pending' NOT NULL 
                            CHECK (training_status IN ('pending','training','completed','failed')),
    training_log_path       TEXT,
    training_metric         JSONB,
    training_progress       JSONB,
    license_type            VARCHAR(30) DEFAULT 'personal' NOT NULL 
                            CHECK (license_type IN ('personal','commercial','exclusive')),
    valid_from              DATE DEFAULT CURRENT_DATE NOT NULL,
    valid_to                DATE,
    generation_cost_tokens  BIGINT NOT NULL DEFAULT 0
                            CHECK (generation_cost_tokens >= 0),
    usage_count             INT DEFAULT 0 NOT NULL,
    is_flagged              BOOLEAN DEFAULT FALSE NOT NULL,
    is_active               BOOLEAN DEFAULT TRUE NOT NULL,
    created_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_artist_style_name UNIQUE (artist_id, name)
);

-- 인덱스
CREATE INDEX idx_styles_artist ON styles(artist_id, is_active);
CREATE INDEX idx_styles_status ON styles(training_status);
CREATE INDEX idx_styles_active ON styles(is_active, created_at DESC)
    WHERE is_active = true;
CREATE INDEX idx_styles_usage ON styles(usage_count DESC, created_at DESC);
```

**주요 컬럼**:
- `training_status`: 학습 상태 (pending → training → completed)
- `training_progress`: 학습 진행 상황 (JSONB)
  - 예시: `{"current_epoch": 50, "total_epochs": 100, "progress_percent": 50, "estimated_seconds": 900, "last_updated": "2025-01-15T12:00:00Z"}`
  - Training Server가 30초마다 업데이트
  - NULL이면 진행 정보 없음 (pending 또는 completed 상태)
- `model_path`: LoRA 모델 파일 경로 (S3)
- `generation_cost_tokens`: 이미지 1장당 토큰 (작가 설정)
- `usage_count`: 실제 생성 횟수 (캐싱 컬럼, generations 테이블 집계)
  - 이미지 생성 완료 시 자동 증가
  - popular 정렬에 사용

**비즈니스 규칙**:
- MVP: 작가당 1개 스타일만 생성 가능
- training_status='completed'일 때만 생성 가능
- ON DELETE RESTRICT: 사용 중인 스타일 삭제 불가
- usage_count는 애플리케이션 또는 트리거에서 관리

---

### artworks

```sql
CREATE TABLE artworks (
    id                      BIGSERIAL PRIMARY KEY,
    style_id                BIGINT NOT NULL 
                            REFERENCES styles(id) ON DELETE CASCADE,
    image_url               TEXT NOT NULL,
    processed_image_url     TEXT,
    is_valid                BOOLEAN DEFAULT TRUE NOT NULL,
    validation_reason       TEXT,
    created_at              TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 인덱스
CREATE INDEX idx_artworks_style ON artworks(style_id);
CREATE INDEX idx_artworks_valid ON artworks(is_valid) WHERE is_valid = true;
```

**주요 컬럼**:
- `image_url`: 원본 이미지 (S3)
- `processed_image_url`: 전처리된 이미지
- `is_valid`: 검증 통과 여부 (형식, 해상도, NSFW)

**비즈니스 규칙**:
- 스타일당 10~100장 필요
- is_valid=true인 이미지만 학습에 사용

---

## generation 스키마

### generations

```sql
CREATE TABLE generations (
    id                  BIGSERIAL PRIMARY KEY,
    user_id             BIGINT NOT NULL 
                        REFERENCES users(id) ON DELETE CASCADE,
    style_id            BIGINT 
                        REFERENCES styles(id) ON DELETE RESTRICT,
    aspect_ratio        VARCHAR(10) DEFAULT '1:1' NOT NULL,
    seed                BIGINT,
    consumed_tokens     BIGINT DEFAULT 0 NOT NULL,
    result_url          TEXT,
    status              VARCHAR(20) DEFAULT 'queued' NOT NULL
                        CHECK (status IN ('queued','processing','retrying','completed','failed')),
    generation_progress JSONB, 
    description         TEXT,
    like_count          INT DEFAULT 0 NOT NULL,
    comment_count       INT DEFAULT 0 NOT NULL,
    is_public           BOOLEAN DEFAULT FALSE NOT NULL,
    created_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at          TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 인덱스
CREATE INDEX idx_generations_user ON generations(user_id, created_at DESC);
CREATE INDEX idx_generations_style ON generations(style_id, status);
CREATE INDEX idx_generations_status ON generations(status);
CREATE INDEX idx_generations_public ON generations(is_public, created_at DESC) 
    WHERE is_public = true;
```

**주요 컬럼**:
- `status`: 처리 상태 (queued → processing → completed/failed/retrying)
  - `queued`: 대기 중
  - `processing`: 생성 중
  - `retrying`: 재시도 중 (실패 후 자동 재시도)
  - `completed`: 완료
  - `failed`: 최종 실패 (3회 재시도 후)
- `generation_progress`: 생성 진행 상황 (JSONB)
  - 예시: `{"progress_percent": 75, "current_step": 38, "total_steps": 50, "last_updated": "2025-01-15T12:00:05Z"}`
  - Inference Server가 업데이트
  - NULL이면 진행 정보 없음 (queued 또는 completed 상태)
- `result_url`: 생성된 이미지 URL (S3)
- `is_public`: 공개 여부 (기본: false)
- `like_count`, `comment_count`: 캐싱 컬럼

**비즈니스 규칙**:
- 생성 전 토큰 차감 (atomic)
- 실패 시 최대 3회 자동 재시도 (GPU OOM, 타임아웃 등)
- 재시도 실패 시 토큰 전액 환불
- style_id는 RESTRICT (스타일 삭제 방지)

---

## community 스키마

### follows

```sql
CREATE TABLE follows (
    id              BIGSERIAL PRIMARY KEY,
    follower_id     BIGINT NOT NULL 
                    REFERENCES users(id) ON DELETE CASCADE,
    following_id    BIGINT NOT NULL 
                    REFERENCES users(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    CONSTRAINT no_self_follow CHECK (follower_id != following_id),
    CONSTRAINT unique_follow_pair UNIQUE (follower_id, following_id)
);

-- 인덱스
CREATE INDEX idx_follows_follower ON follows(follower_id);
CREATE INDEX idx_follows_following ON follows(following_id);
```

**비즈니스 규칙**:
- 자기 팔로우 불가
- 중복 팔로우 불가
- 언팔로우 = 레코드 삭제

---

### likes

```sql
CREATE TABLE likes (
    id              BIGSERIAL PRIMARY KEY,
    user_id         BIGINT NOT NULL 
                    REFERENCES users(id) ON DELETE CASCADE,
    generation_id   BIGINT NOT NULL 
                    REFERENCES generations(id) ON DELETE CASCADE,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    CONSTRAINT unique_like UNIQUE (user_id, generation_id)
);

-- 인덱스
CREATE INDEX idx_likes_generation ON likes(generation_id);
CREATE INDEX idx_likes_user ON likes(user_id, created_at DESC);
```

**비즈니스 규칙**:
- 중복 좋아요 불가
- 좋아요 시 generations.like_count 증가 (트리거 또는 애플리케이션)

---

### comments

```sql
CREATE TABLE comments (
    id              BIGSERIAL PRIMARY KEY,
    generation_id   BIGINT NOT NULL 
                    REFERENCES generations(id) ON DELETE CASCADE,
    user_id         BIGINT NOT NULL 
                    REFERENCES users(id) ON DELETE CASCADE,
    parent_id       BIGINT 
                    REFERENCES comments(id) ON DELETE CASCADE,
    content         TEXT NOT NULL,
    like_count      INT DEFAULT 0 NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 인덱스
CREATE INDEX idx_comments_generation ON comments(generation_id, created_at DESC);
CREATE INDEX idx_comments_user ON comments(user_id);
CREATE INDEX idx_comments_parent ON comments(parent_id);
```

**주요 컬럼**:
- `parent_id`: NULL이면 일반 댓글, 값 있으면 대댓글
- `like_count`: 댓글 좋아요 수 (MVP 미구현, 향후 Phase 2 예정)

**비즈니스 규칙**:
- MVP: 1단계 대댓글만 허용
- 댓글 삭제 시 대댓글도 CASCADE 삭제
- 작성 시 generations.comment_count 증가
- **댓글 좋아요 기능**: MVP에서는 구현하지 않음, `like_count`는 0으로 유지

---

## tagging 스키마

### tags

```sql
CREATE TABLE tags (
    id              BIGSERIAL PRIMARY KEY,
    name            VARCHAR(100) UNIQUE NOT NULL,
    usage_count     INT DEFAULT 0 NOT NULL,
    is_active       BOOLEAN DEFAULT TRUE NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 인덱스
CREATE INDEX idx_tags_name ON tags(name) WHERE is_active = true;
CREATE INDEX idx_tags_active ON tags(is_active, usage_count DESC);
```

**비즈니스 규칙**:
- 영어만 허용 (Stable Diffusion 프롬프트)
- 소문자 저장 (자동 변환)
- usage_count는 M:N 테이블 집계

---

### style_tags

```sql
CREATE TABLE style_tags (
    style_id    BIGINT NOT NULL REFERENCES styles(id) ON DELETE CASCADE,
    tag_id      BIGINT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    sequence    INT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    PRIMARY KEY (style_id, tag_id),
    UNIQUE (style_id, sequence)
);

CREATE INDEX idx_style_tags_tag ON style_tags(tag_id);
```

**비즈니스 규칙**:
- sequence: 태그 순서 보존
- 복합 PK: (style_id, tag_id)

---

### artwork_tags

```sql
CREATE TABLE artwork_tags (
    artwork_id  BIGINT NOT NULL REFERENCES artworks(id) ON DELETE CASCADE,
    tag_id      BIGINT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    sequence    INT NOT NULL,
    created_at  TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    PRIMARY KEY (artwork_id, tag_id),
    UNIQUE (artwork_id, sequence)
);

CREATE INDEX idx_artwork_tags_tag ON artwork_tags(tag_id);
```

---

### generation_tags

```sql
CREATE TABLE generation_tags (
    generation_id   BIGINT NOT NULL REFERENCES generations(id) ON DELETE CASCADE,
    tag_id          BIGINT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
    sequence        INT NOT NULL,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL,
    
    PRIMARY KEY (generation_id, tag_id),
    UNIQUE (generation_id, sequence)
);

CREATE INDEX idx_generation_tags_tag ON generation_tags(tag_id);
```

**비즈니스 규칙**:
- 태그로 생성물 검색 가능
- sequence로 프롬프트 재구성

---

## system 스키마

### notifications

```sql
CREATE TABLE notifications (
    id              BIGSERIAL PRIMARY KEY,
    recipient_id    BIGINT NOT NULL 
                    REFERENCES users(id) ON DELETE CASCADE,
    actor_id        BIGINT 
                    REFERENCES users(id) ON DELETE CASCADE,
    type            VARCHAR(30) NOT NULL
                    CHECK (type IN ('follow','like','comment','generation_complete','generation_failed','style_training_complete','style_training_failed')),
    target_type     VARCHAR(30),
    target_id       BIGINT,
    is_read         BOOLEAN DEFAULT FALSE NOT NULL,
    metadata        JSONB,
    created_at      TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP NOT NULL
);

-- 인덱스
CREATE INDEX idx_notifications_recipient ON notifications(recipient_id, is_read, created_at DESC);
CREATE INDEX idx_notifications_actor ON notifications(actor_id);
```

**알림 타입**:
- `follow`: A가 나를 팔로우 (actor 존재)
- `like`: A가 내 게시물 좋아요 (actor 존재)
- `comment`: A가 댓글 작성 (actor 존재)
- `generation_complete`: 이미지 생성 완료 (시스템, actor=null)
- `generation_failed`: 이미지 생성 실패 (시스템, actor=null)
- `style_training_complete`: 스타일 학습 완료 (시스템, actor=null)
- `style_training_failed`: 스타일 학습 실패 (시스템, actor=null)

**비즈니스 규칙**:
- actor_id=NULL: 시스템 알림
- metadata: 추가 정보 (댓글 미리보기 등)
- 30일 이상 읽은 알림 자동 삭제

---

## 전체 테이블 생성 순서

```sql
-- 1. 독립 테이블
CREATE TABLE users;
CREATE TABLE tags;

-- 2. users 의존
CREATE TABLE artists;
CREATE TABLE styles;
CREATE TABLE generations;
CREATE TABLE follows;
CREATE TABLE notifications;

-- 3. styles 의존
CREATE TABLE artworks;
CREATE TABLE transactions;

-- 4. generations 의존
CREATE TABLE likes;
CREATE TABLE comments;

-- 5. M:N 테이블
CREATE TABLE style_tags;
CREATE TABLE artwork_tags;
CREATE TABLE generation_tags;

-- 6. 외부 시스템
CREATE TABLE purchases;
```

---

[← 돌아가기](README.md) | [쿼리 예제 보기](guides/QUERIES.md)