# Claude Development Assistant Guide

## Overview

이 파일은 Claude가 Style License 프로젝트를 개발할 때 따라야 할 워크플로우를 정의합니다.

---

## Initial Setup

**첫 작업 시작 전 필수 읽기:**

1. **Read [TECHSPEC.md](TECHSPEC.md)** - 전체 시스템 구조, 아키텍처, 핵심 Context 이해
   - Section 4: 시스템 아키텍처 및 컴포넌트 간 관계
   - Section 5: 데이터 모델 및 스키마
   - Section 6: API 설계
2. **Read [PLAN.md](PLAN.md)** - 현재 진행 중인 Milestone 확인

**항상 참조:**
- [docs/database/README.md](docs/database/README.md) - DB 스키마 확인 시
- [docs/API.md](docs/API.md) - API 엔드포인트 구현 시
- [docs/PATTERNS.md](docs/PATTERNS.md) - 공통 코드 패턴 확인 시

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

### Step 3: Implement

1. **Read Task Details**
   - Task의 **작업 내용**, **완료 조건**, **참조 문서** 확인
   - 체크되지 않은 첫 번째 Subtask 찾기

2. **Write Test First (TDD 방식, 해당하는 경우)**
   - Backend: `apps/backend/app/tests/test_*.py`
   - Frontend: `apps/frontend/src/**/*.test.js` 또는 Playwright E2E
   - Training/Inference: `apps/*/tests/test_*.py`

3. **Implement Code**
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

### Step 4: Mark Complete

1. **App PLAN.md 업데이트**
   - 완료한 Subtask에 `[x]` 체크
   - 해당 작업의 Commit ID 기록 (선택)

2. **Root PLAN.md 업데이트**
   - 해당 Task의 모든 Subtask가 완료되었으면
   - Root PLAN.md에서 해당 Task에 `[x]` 체크

3. **Milestone 완료 확인**
   - Milestone의 모든 Task가 체크되었으면
   - Milestone의 **Exit Criteria** 확인
   - 모두 만족하면 Milestone Status를 `DONE`으로 변경
   - 다음 Milestone의 Status를 `IN_PROGRESS`로 변경

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

#### 5. Implement

**5.1. Write Test:**
```python
# apps/backend/app/tests/test_token_service.py
def test_concurrent_token_consumption():
    # 100개 동시 요청 시뮬레이션
    ...
```

**5.2. Implement Code:**
```python
# apps/backend/app/services/token_service.py
@transaction.atomic
def consume_tokens(user_id, amount, ...):
    user = User.objects.select_for_update().get(id=user_id)
    ...
```

**5.3. Run Checks:**
```bash
cd apps/backend
black app/
pylint app/services/token_service.py
python manage.py test app.tests.test_token_service
```

**5.4. Iterate until all pass**

#### 6. Mark Complete

**apps/backend/PLAN.md:**
```markdown
- [x] consume_tokens() with SELECT FOR UPDATE
```

**PLAN.md (when all subtasks done):**
```markdown
- [x] CP-M2-3: Token Transaction Atomicity
```

---

## Key Principles

### 🎯 Token Efficiency
- **Always start with TECHSPEC.md** (한 번만 읽기)
- **Load CODE_GUIDE.md once per app** (여러 Task에 재사용)
- **Lazy load docs/** (필요할 때만 읽기)
- **Don't load cross-app context** (Backend 작업 시 Frontend CODE_GUIDE 읽지 않기)

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
1. Subtask 완료 → App PLAN.md에 `[x]` 체크
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
1. 사용자에게 명확화 요청
2. 임시로 합리적인 가정 하에 진행
3. 작성한 코드에 TODO 주석으로 표시

---

## Notes

- 이 가이드는 **워크플로우의 일관성**을 위한 것입니다
- 상황에 따라 유연하게 조정 가능합니다
- 사용자의 추가 지시사항이 있으면 우선합니다
- 불명확한 부분은 언제든 질문하세요

---