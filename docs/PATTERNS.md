# Common Code Patterns

> 이 문서는 프로젝트 전체에서 공통으로 사용하는 패턴입니다.  
> 각 앱의 세부 패턴은 `apps/*/GUIDE.md`를 참조하세요.

## API Response Format

**Success Response**:
```json
{
  "data": { ... },
  "meta": {
    "page": 1,
    "page_size": 20,
    "total": 100
  }
}
```

**Error Response**:
```json
{
  "error": {
    "code": "INVALID_INPUT",
    "message": "Token balance insufficient",
    "details": { "required": 100, "current": 50 }
  }
}
```

## RabbitMQ Message Format

**Training Task**:
```json
{
  "task_id": "uuid",
  "model_id": 123,
  "images": ["s3://bucket/image1.jpg", ...],
  "tags": ["watercolor", "portrait"],
  "callback_url": "https://api/models/123/status"
}
```

## Database Naming Conventions

- Tables: `snake_case` plural (e.g., `style_models`, `token_transactions`)
- Columns: `snake_case` (e.g., `created_at`, `user_type`)
- Indexes: `idx_{table}_{column}` (e.g., `idx_users_google_id`)
- Foreign keys: `{related_table}_id` (e.g., `artist_id`, `style_model_id`)

## Git Commit Convention
```
feat: Add style model API
fix: Resolve token race condition
docs: Update DATABASE.md schema
test: Add token service unit tests
refactor: Extract signature logic to service
```

---