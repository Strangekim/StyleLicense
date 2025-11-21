# Claude Development Assistant Guide

## Overview

이 파일은 Claude가 Style License 프로젝트를 개발할 때 따라야 할 워크플로우를 정의합니다.

---

## Initial Setup

**첫 작업 시작 전 필수 읽기:**

1. **Read [TECHSPEC_SUMMARY.md](TECHSPEC_SUMMARY.md)** - 전체 시스템 핵심 요약 (필수, 45분 내 파악 가능)
   - Section 1-2: 프로젝트 정체성, 아키텍처, 기술 스택
   - **Section 4**: **프론트엔드 페이지 9개 목록** (페이지 누락 방지!)
   - Section 3.7: API 그룹 7개 개요 (API 누락 방지!)
   - Section 3.8: 에러 코드 체계 (일관된 에러 처리)
   - Section 3.9-3.11: 보안, 성능, 테스트 전략
2. **Read [PLAN.md](PLAN.md)** - 현재 진행 중인 Milestone 확인
3. **필요시 Read [TECHSPEC.md](TECHSPEC.md)** - 상세 명세 (선택적, SUMMARY의 앵커 링크 활용)
   - Section 6: API 전체 스펙 (특정 엔드포인트 구현 시)
   - Section 7: 프론트엔드 아키텍처 전체 (프론트엔드 구현 시)
   - Section 10-13: 보안/에러/성능/테스트 상세 (필요 시)

**항상 참조:**
- [docs/database/README.md](docs/database/README.md) - DB 스키마 확인 시
- [docs/API.md](docs/API.md) - API 엔드포인트 구현 시
- [docs/PATTERNS.md](docs/PATTERNS.md) - 공통 코드 패턴 확인 시

**토큰 절약 전략:**
- **TECHSPEC_SUMMARY.md (300줄)을 먼저 읽어 전체 맵 파악**
- TECHSPEC.md (1853줄)은 필요한 섹션만 선택적으로 읽기
- 예: Frontend 페이지 구현 → SUMMARY Section 4 확인 → 필요시 TECHSPEC Section 7 전체 읽기

---

## Workflow: "go" Command

사용자가 **"go"** 라고 입력하면 다음 순서를 따릅니다:

### Step 1: Find Next Task

1. **[PLAN.md](PLAN.md)** 열기
2. 현재 `Status: IN_PROGRESS` 또는 `Status: PLANNED`인 Milestone 찾기
3. 해당 Milestone의 **Critical Path (CP-*)** 확인
   - Critical Path 작업이 남아있으면 → Critical Path 우선
   - Critical Path가 모두 완료되었으면 → Parallel Tasks (PT-*) 진행
4. 체크되지 않은 `[ ]` 첫 번째 작업 찾기
5. 해당 작업의 **Reference** 링크 따라가기 (예: `apps/backend/PLAN.md#m2-style-model-api`)

### Step 2: Read App-Specific Documents

**작업이 Backend인 경우:**
1. **[apps/backend/README.md](apps/backend/README.md)** - Backend 아키텍처 이해
2. **[apps/backend/PLAN.md](apps/backend/PLAN.md)** - 세부 Subtask 확인
3. **[apps/backend/CODE_GUIDE.md](apps/backend/CODE_GUIDE.md)** - 코드 작성 패턴 학습

**작업이 Frontend인 경우:**
1. **[apps/frontend/README.md](apps/frontend/README.md)** - Frontend 아키텍처 이해
2. **[apps/frontend/PLAN.md](apps/frontend/PLAN.md)** - 세부 Subtask 확인
3. **[apps/frontend/CODE_GUIDE.md](apps/frontend/CODE_GUIDE.md)** - 코드 작성 패턴 학습

**작업이 Training Server인 경우:**
1. **[apps/training-server/README.md](apps/training-server/README.md)** - 학습 파이프라인 이해
2. **[apps/training-server/PLAN.md](apps/training-server/PLAN.md)** - 세부 Subtask 확인
3. **[apps/training-server/CODE_GUIDE.md](apps/training-server/CODE_GUIDE.md)** - 코드 작성 패턴 학습

**작업이 Inference Server인 경우:**
1. **[apps/inference-server/README.md](apps/inference-server/README.md)** - 추론 파이프라인 이해
2. **[apps/inference-server/PLAN.md](apps/inference-server/PLAN.md)** - 세부 Subtask 확인
3. **[apps/inference-server/CODE_GUIDE.md](apps/inference-server/CODE_GUIDE.md)** - 코드 작성 패턴 학습

### Step 3: Verify Specification Compliance

⚠️ **구현 전 필수 검증 단계** - 이 단계를 건너뛰면 명세 위반이 발생합니다!

#### 3.1. 명세 우선 원칙

**절대 규칙:**
- ✅ **프로젝트 명세 > 프레임워크 관습**
- ✅ **TECHSPEC.md, TABLES.md가 단일 진실 공급원(Single Source of Truth)**
- ❌ "Django/Vue/FastAPI에서 보통 이렇게 해" ← 명세 확인 없이 적용 금지

#### 3.2. Backend 모델 작성 시 필수 체크리스트

**Database 모델을 작성할 때 (Django Model, SQLAlchemy 등):**

- [ ] **Step 1**: `docs/database/TABLES.md` 열기
- [ ] **Step 2**: 해당 테이블의 CREATE TABLE 문 확인
- [ ] **Step 3**: 컬럼 목록 확인
  ```
  예: users 테이블
  - id ✓
  - username ✓
  - email ✓
  - provider ✓
  - provider_user_id ✓
  - password ✗ (없음!)
  ```
- [ ] **Step 4**: 각 컬럼의 데이터 타입, 제약조건 확인
  ```sql
  username VARCHAR(50) UNIQUE NOT NULL
  → Django: models.CharField(max_length=50, unique=True)
  ```
- [ ] **Step 5**: 프레임워크 기본 필드와 명세 비교
  ```python
  # ❌ 잘못된 예
  class User(AbstractBaseUser):  # password 자동 추가

  # ✅ 올바른 예 (명세에 password 없음)
  class User(models.Model):  # password 없음
  ```

#### 3.3. Migration 생성 후 필수 검증

**Django: makemigrations 후**
```bash
python manage.py makemigrations
# → migrations/0001_initial.py 생성됨
```

- [ ] **Step 1**: 생성된 migration 파일 열기
- [ ] **Step 2**: `operations` 섹션의 `CreateModel` 확인
- [ ] **Step 3**: `fields` 리스트와 TABLES.md 대조
  ```python
  # migrations/0001_initial.py
  operations = [
      migrations.CreateModel(
          name='User',
          fields=[
              ('id', models.BigAutoField(primary_key=True)),
              ('username', models.CharField(max_length=50, unique=True)),
              ('password', models.CharField(max_length=128)),  # ← 이게 명세에 있는가?
          ]
      )
  ]
  ```
- [ ] **Step 4**: 명세에 없는 필드 발견 시
  1. 모델 수정 (필드 제거 또는 비활성화)
  2. Migration 재생성
  3. 재검증

**FastAPI/SQLAlchemy: alembic revision 후**
- 동일한 방식으로 `upgrade()` 함수의 `op.create_table()` 검증

#### 3.4. API 엔드포인트 작성 시 필수 체크리스트

- [ ] **Step 1**: `docs/API.md` 또는 `TECHSPEC.md` Section 6 확인
- [ ] **Step 2**: 해당 엔드포인트가 명세에 존재하는가?
  ```
  예: POST /api/auth/login (email/password)
  → TECHSPEC.md 확인 → "Google OAuth only, 자체 로그인 없음"
  → 이 엔드포인트는 명세 위반!
  ```
- [ ] **Step 3**: 명세에 없는 엔드포인트를 추가하려면
  1. **반드시 사용자에게 먼저 물어보기** (한국어로)
  2. 사용자 승인 후 TECHSPEC.md / API.md 업데이트
  3. 그 다음 구현

#### 3.5. 사용자 요구가 명세와 충돌할 때

**시나리오 예시:**
```
사용자: "Postman으로 API 테스트하고 싶어요. 로그인 엔드포인트 만들어주세요."
Claude 사고: "Google OAuth는 브라우저 필요... 간단하게 email/password 로그인 추가?"
```

**❌ 절대 하지 말 것:**
- 명세 확인 없이 편의 기능 추가
- "개발용", "테스트용"이라는 명목으로 명세 위반

**✅ 올바른 접근:**
1. **명세 확인**
   ```
   TECHSPEC.md → "자체 로그인 없음"
   TABLES.md → users 테이블에 password 컬럼 없음
   ```

2. **사용자에게 명확히 설명 (한국어)**
   ```
   "현재 명세(TECHSPEC.md)에는 'Google OAuth only, 자체 로그인 없음'으로 정의되어 있습니다.
   email/password 로그인을 추가하려면 명세를 수정해야 합니다.

   대신 다음 방법으로 Postman 테스트가 가능합니다:
   1. Django Admin에서 수동 세션 생성
   2. 테스트용 세션 쿠키 직접 발급
   3. 브라우저에서 Google OAuth 완료 후 쿠키 복사

   어떤 방법을 사용하시겠습니까?"
   ```

3. **사용자 결정 대기**
   - 명세 수정 승인 → TECHSPEC.md 업데이트 후 구현
   - 대안 선택 → 명세 유지하며 대안 제공

#### 3.6. 프레임워크별 주의사항

**Django:**
- `AbstractBaseUser`: password, last_login 자동 추가
- `AbstractUser`: 더 많은 기본 필드 (first_name, last_name, email 등)
- 명세에 없는 필드는 `None`으로 비활성화 또는 `models.Model` 직접 상속

**Vue Router:**
- 기본 라우팅 패턴이 아닌 TECHSPEC_SUMMARY.md Section 4의 페이지 정의 우선

**FastAPI:**
- Pydantic 모델의 자동 검증이 명세의 제약조건과 일치하는지 확인

#### 3.7. Frontend 페이지 작성 시 필수 체크리스트

**PLAN.md 작성 또는 페이지 구현 전:**

- [ ] **Step 1**: `TECHSPEC_SUMMARY.md` Section 4 열기
- [ ] **Step 2**: 필수 페이지 목록 9개 확인
  ```
  1. Main Page
  2. Feed Detail Page (Comment Modal 포함)
  3. Search & Following Artist Page
  4. Style Detail Page
  5. My Page (공개/비공개 피드 그리드)
  6. Edit/Create Style Page
  7. Edit Profile
  8. Payment Page
  9. Notification Page
  ```
- [ ] **Step 3**: `apps/frontend/PLAN.md`에 모든 페이지가 포함되었는지 검증
- [ ] **Step 4**: 각 페이지의 핵심 섹션 확인 (Modal, Grid, 검색창 등)
- [ ] **Step 5**: 명세에 없는 페이지 추가 또는 제외 시:
  1. **반드시 사용자에게 먼저 물어보기** (한국어로)
  2. 사용자 승인 후 `TECHSPEC.md` Section 7.2 업데이트
  3. `TECHSPEC_SUMMARY.md` Section 4도 업데이트
  4. 그 다음 `PLAN.md` 업데이트

**예시:**
```
❌ 잘못된 예:
- PLAN.md에 "Feed Detail Page - deferred to post-MVP" 작성
- TECHSPEC_SUMMARY.md 확인 없이 "MVP에 너무 복잡하니 제외" 판단

✅ 올바른 예:
1. TECHSPEC_SUMMARY.md Section 4 확인 → "Feed Detail Page 필수"
2. PLAN.md에 페이지 포함 또는
3. 사용자에게 "명세에는 Feed Detail Page가 필수인데 제외하려면 TECHSPEC 수정 필요" 문의
```

---

### Step 4: Implement

1. **Read Task Details**
   - Task의 **작업 내용**, **완료 조건**, **참조 문서** 확인
   - 체크되지 않은 첫 번째 Subtask 찾기

2. **Write Test First (TDD 방식, 해당하는 경우)**
   - Backend: `apps/backend/app/tests/test_*.py`
   - Frontend: `apps/frontend/src/**/*.test.js` 또는 Playwright E2E
   - Training/Inference: `apps/*/tests/test_*.py`

3. **Implement Code**
   - **Step 3의 명세 검증 체크리스트를 먼저 완료**
   - **CODE_GUIDE.md**의 패턴을 따라 코드 작성
   - **PATTERNS.md**의 공통 규칙 준수
   - 파일 위치는 **해당 앱의 README.md**의 Directory Structure 참고
     - Backend: [apps/backend/README.md](apps/backend/README.md)
     - Frontend: [apps/frontend/README.md](apps/frontend/README.md)
     - Training: [apps/training-server/README.md](apps/training-server/README.md)
     - Inference: [apps/inference-server/README.md](apps/inference-server/README.md)

4. **Run Quality Checks**

   **Backend (Django):**
```bash
   cd apps/backend
   # Format
   black app/
   # Lint
   pylint app/
   # Test
   python manage.py test
```

   **Frontend (Vue):**
```bash
   cd apps/frontend
   # Format
   npm run format
   # Lint
   npm run lint
   # Test
   npm run test
```

   **Training/Inference Server (Python):**
```bash
   cd apps/training-server  # or apps/inference-server
   # Format
   black .
   # Lint
   pylint *.py
   # Test
   pytest
```

5. **Iterate Until Passing**
   - 테스트 실패 시: 코드 수정 후 다시 실행
   - Lint 에러 시: 에러 수정 후 다시 실행
   - 모든 체크가 통과할 때까지 반복

### Step 5: Finalize and Commit

⚠️ **중요**: 아래 순서를 **반드시 따라야** 합니다. 순서를 지키지 않으면 PLAN.md가 동기화되지 않습니다.

#### 5.1. 코드 변경사항 커밋

1.  **개발 브랜치로 전환 및 동기화**:
    *   `git checkout dev` 명령어로 공용 개발 브랜치인 `dev`로 전환합니다.
    *   `git pull origin dev` 명령어로 최신 코드를 반영합니다.

2.  **변경사항 스테이징 및 커밋 (코드만)**:
    *   `git add .` 명령어로 변경된 모든 파일을 스테이징합니다.
    *   `git commit -m "feat(app): description"` 형식으로 커밋 메시지를 작성하여 커밋합니다.
    *   ⚠️ **주의**: PLAN.md 파일은 **아직 커밋하지 않습니다**.

3.  **원격 저장소에 푸시**:
    *   `git push origin dev` 명령어로 `dev` 브랜치에 변경사항을 푸시합니다.

4.  **커밋 해시 저장**:
    *   `git rev-parse HEAD` 명령어로 방금 생성한 커밋의 고유 해시값을 가져옵니다.
    *   예: `a1b2c3d` (처음 7자리만 사용)

#### 5.2. PLAN.md 업데이트 (⚠️ 반드시 순서대로!)

**체크리스트**를 따라 진행하세요:

- [ ] **Step 1**: `apps/{app-name}/PLAN.md` 열기
  - 예: `apps/backend/PLAN.md`, `apps/frontend/PLAN.md`

- [ ] **Step 2**: 완료한 Subtask 찾기
  - 현재 작업한 섹션 (예: M1-Initialization, M2-Token-Service 등)

- [ ] **Step 3**: Subtask에 체크 및 커밋 해시 기록
  ```markdown
  - [x] GET /api/tokens/balance endpoint (Commit: a1b2c3d)
  - [x] POST /api/tokens/purchase endpoint (Commit: a1b2c3d)
  ```

- [ ] **Step 4**: 섹션 상태 업데이트 (필요시)
  - 모든 subtask가 완료되었다면 `Status: PLANNED` → `Status: DONE`으로 변경

- [ ] **Step 5**: `PLAN.md` (루트) 열기

- [ ] **Step 6**: 상위 태스크 확인
  - App PLAN.md의 모든 subtask가 완료되었다면, Root PLAN.md의 해당 태스크도 체크
  - 예: `apps/backend/PLAN.md#m1-initialization`의 모든 subtask 완료 → Root `PLAN.md`의 `PT-M1-Backend` 체크

- [ ] **Step 7**: Root PLAN.md에 커밋 해시 기록
  ```markdown
  - [x] CP-M2-3: Token Transaction Atomicity (Commit: a1b2c3d)
  ```

#### 5.3. PLAN.md 커밋

1.  **PLAN.md 파일 스테이징 및 커밋**:
    ```bash
    git add apps/{app-name}/PLAN.md PLAN.md
    git commit -m "docs: update PLAN.md - {task-name} completed (commit a1b2c3d)"
    git push origin dev
    ```

#### 5.4. 사용자에게 보고

*   "작업이 완료되어 `dev` 브랜치에 커밋(a1b2c3d)하고 푸시했습니다. `apps/{app-name}/PLAN.md`와 `PLAN.md`에 커밋 정보를 기록했습니다." 형식으로 보고합니다.

---

**⚠️ 자주 하는 실수**:

**PLAN.md 관련:**
- ❌ Root PLAN.md만 업데이트하고 App PLAN.md를 빠뜨림
- ❌ 커밋 해시를 기록하지 않음
- ❌ App PLAN.md와 Root PLAN.md가 불일치
- ❌ PLAN.md 업데이트를 별도로 커밋하지 않음

**명세 준수 관련 (치명적!):**
- ❌ TABLES.md 확인 없이 Django AbstractBaseUser 사용 → password 자동 추가
- ❌ Migration 생성 후 명세와 대조하지 않음
- ❌ "개발 편의"를 이유로 명세에 없는 API 엔드포인트 추가 (예: email/password 로그인)
- ❌ **TECHSPEC_SUMMARY.md Section 4 확인 없이 Frontend 페이지 제외** (예: Feed Detail, Profile, Payment 등)
- ❌ 프레임워크 관습을 명세보다 우선시
- ❌ 사용자 요구를 명세 확인 없이 바로 구현

---

## Example Workflow

### User Input:
```
go
```

### Claude Process:

#### 1. Read PLAN.md
```
M2: Core Backend - Status: IN_PROGRESS
Critical Path:
  - [x] CP-M2-1: API Foundation
  - [x] CP-M2-2: RabbitMQ Integration
  - [ ] CP-M2-3: Token Transaction Atomicity  ← 다음 작업
```

#### 2. Navigate to Task
```
CP-M2-3 → Reference: apps/backend/PLAN.md#m2-token-service
```

#### 3. Read Backend Docs
```
apps/backend/README.md (아키텍처 파악)
apps/backend/PLAN.md#m2-token-service (세부 Task)
apps/backend/CODE_GUIDE.md (코드 패턴)
```

#### 4. Find Subtask
```markdown
### M2-Token-Service

- [x] TokenTransaction 모델 생성
- [x] TokenService 클래스 생성
- [ ] consume_tokens() with SELECT FOR UPDATE  ← 다음 Subtask
- [ ] 동시성 테스트 작성
```

#### 5. Verify Specification (Step 3)

**5.1. Check TABLES.md:**
```bash
# TokenTransaction 모델 작성 전 docs/database/TABLES.md 확인
# transactions 테이블 컬럼 목록 확인
# ✓ 명세와 일치하는지 검증 완료
```

#### 6. Implement (Step 4)

**6.1. Write Test:**
```python
# apps/backend/app/tests/test_token_service.py
def test_concurrent_token_consumption():
    # 100개 동시 요청 시뮬레이션
    ...
```

**6.2. Implement Code:**
```python
# apps/backend/app/services/token_service.py
@transaction.atomic
def consume_tokens(user_id, amount, ...):
    user = User.objects.select_for_update().get(id=user_id)
    ...
```

**6.3. Run Checks:**
```bash
cd apps/backend
black app/
pylint app/services/token_service.py
python manage.py test app.tests.test_token_service
```

**6.4. Iterate until all pass**

#### 7. Finalize and Commit (Step 5)

**7.1. Checkout and Commit**
```bash
git checkout dev
git pull origin dev
git add .
git commit -m "feat(backend): implement consume_tokens with SELECT FOR UPDATE"
git push origin dev
```

**7.2. Record Commit Hash**
(git rev-parse HEAD 실행 후 나온 해시가 `a1b2c3d`라고 가정)

**apps/backend/PLAN.md:**
```markdown
- [x] consume_tokens() with SELECT FOR UPDATE (Commit: a1b2c3d)
```

**PLAN.md (when all subtasks done):**
```markdown
- [x] CP-M2-3: Token Transaction Atomicity
```

---

## Key Principles

### 🎯 Token Efficiency
- **Always start with TECHSPEC_SUMMARY.md** (300줄, 빠른 전체 맵 파악)
- **Lazy load TECHSPEC.md** (1853줄, 필요한 섹션만 선택적 읽기)
  - Frontend 페이지 구현 시: Section 7 전체 읽기
  - API 구현 시: Section 6 해당 그룹만 읽기
  - 보안 관련: Section 10 읽기
  - 성능/테스트: Section 12-13 읽기
- **Load CODE_GUIDE.md once per app** (여러 Task에 재사용)
- **Lazy load docs/** (필요할 때만 읽기)
- **Don't load cross-app context** (Backend 작업 시 Frontend CODE_GUIDE 읽지 않기)

### 🔒 Specification Compliance (최우선 원칙)
1. **프로젝트 명세 > 프레임워크 관습** - Django/Vue 일반 패턴보다 TECHSPEC.md가 우선
2. **TABLES.md 필수 검증** - DB 모델 작성 시 컬럼 1:1 매칭 필수
3. **Migration 검증** - makemigrations 후 명세와 대조
4. **명세 없는 기능 추가 금지** - 사용자에게 먼저 물어보기
5. **"개발 편의" 명목 명세 위반 절대 금지** - 테스트용, 임시용도 금지

### 📏 Code Quality
1. **Follow CODE_GUIDE.md patterns** - 일관된 코드 스타일
2. **Run format & lint** - 코드 품질 보장
3. **Write tests first** - TDD 방식 (해당하는 경우)
4. **Check exit criteria** - Task 완료 조건 확인

### 🔄 Iteration
- 테스트 실패 → 코드 수정 → 재실행
- Lint 에러 → 수정 → 재실행
- 모든 체크 통과할 때까지 반복

### ✅ Task Completion
1. Subtask 완료 → App PLAN.md에 `[x]` 체크 및 커밋 해시 기록
2. 모든 Subtask 완료 → Root PLAN.md에 `[x]` 체크
3. Exit Criteria 확인 → 모두 만족 시 Milestone `DONE`

---

## Special Commands

### "go"
다음 미완료 작업 찾아서 구현

### "status"
현재 진행 상황 요약:
- 현재 Milestone
- 완료된 Task 수 / 전체 Task 수
- 다음 작업 미리보기

### "review"
마지막으로 완료한 작업 리뷰:
- 작성한 코드 요약
- 테스트 결과
- 완료 조건 충족 여부

### "plan"
전체 PLAN.md 진행 상황 시각화

---

## Troubleshooting

### Task가 Blocked 상태인 경우
1. **Dependencies** 확인
2. 선행 작업이 완료되지 않았으면 먼저 완료
3. 외부 요인(API 키, 인프라)이면 사용자에게 알림

### Exit Criteria를 만족하지 못하는 경우
1. 각 조건을 하나씩 확인
2. 실패한 조건에 대한 추가 작업 수행
3. 모든 조건 만족 시 Milestone 완료

### 문서가 없거나 불명확한 경우
1. **반드시 한국어로** 사용자에게 명확화 요청
2. 임시로 합리적인 가정 하에 진행
3. 작성한 코드에 TODO 주석으로 표시

---

## Notes

- 이 가이드는 **워크플로우의 일관성**을 위한 것입니다
- 상황에 따라 유연하게 조정 가능합니다
- 사용자의 추가 지시사항이 있으면 우선합니다
- 불명확한 부분은 언제든 질문하세요
- 모든 질문 및 사용자 확인 요청은 **반드시 한국어로** 진행합니다.


---