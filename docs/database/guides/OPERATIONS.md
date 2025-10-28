# OPERATIONS.md

마이그레이션, 성능 최적화, 백업/복구, 모니터링

[← 돌아가기](README.md)

---

## 목차
1. [마이그레이션](#1-마이그레이션)
2. [성능 최적화](#2-성능-최적화)
3. [백업 & 복구](#3-백업--복구)
4. [모니터링](#4-모니터링)
5. [유지보수](#5-유지보수)

---

## 1. 마이그레이션

### 기본 명령어

```bash
# 마이그레이션 파일 생성
python manage.py makemigrations

# 마이그레이션 실행
python manage.py migrate

# SQL 확인 (실행 안 함)
python manage.py sqlmigrate app_name 0001

# 상태 확인
python manage.py showmigrations
```

### Zero-Downtime 배포 (3단계)

#### Phase 1: 호환 가능한 스키마 변경
```python
# Step 1: 새 컬럼 추가 (NULL 허용)
class Migration(migrations.Migration):
    operations = [
        migrations.AddField(
            model_name='generation',
            name='aspect_ratio',
            field=models.CharField(max_length=10, null=True),
        ),
    ]
# → 배포 (구버전 앱은 이 컬럼 무시)
```

#### Phase 2: 데이터 마이그레이션
```python
# Step 2: 기본값 설정
def set_default_ratio(apps, schema_editor):
    Generation = apps.get_model('app', 'Generation')
    Generation.objects.filter(aspect_ratio__isnull=True).update(
        aspect_ratio='1:1'
    )

class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(set_default_ratio),
    ]
# → 배포 (백그라운드 작업)
```

#### Phase 3: 제약 조건 추가
```python
# Step 3: NOT NULL 제약
class Migration(migrations.Migration):
    operations = [
        migrations.AlterField(
            model_name='generation',
            name='aspect_ratio',
            field=models.CharField(max_length=10, default='1:1'),
        ),
    ]
# → 배포 (신버전 앱은 필수값)
```

### 대용량 데이터 마이그레이션

```python
def migrate_large_table(apps, schema_editor):
    """배치 처리로 성능 최적화"""
    Model = apps.get_model('app', 'Model')
    
    batch_size = 1000
    total = Model.objects.count()
    
    for offset in range(0, total, batch_size):
        batch = Model.objects.all()[offset:offset+batch_size]
        
        for obj in batch:
            obj.new_field = calculate_value(obj)
        
        Model.objects.bulk_update(batch, ['new_field'])
        print(f"Processed {offset + len(batch)} / {total}")

class Migration(migrations.Migration):
    operations = [
        migrations.RunPython(migrate_large_table),
    ]
```

### CONCURRENT 인덱스 추가

```python
from django.contrib.postgres.operations import AddIndexConcurrently
from django.db import migrations, models

class Migration(migrations.Migration):
    atomic = False  # CONCURRENT는 트랜잭션 밖에서
    
    operations = [
        AddIndexConcurrently(
            model_name='generation',
            index=models.Index(
                fields=['user', '-created_at'],
                name='idx_gen_user_created'
            ),
        ),
    ]
```

### 배포 체크리스트

```bash
# 1. 로컬 테스트
python manage.py migrate --plan
python manage.py migrate

# 2. 스테이징 테스트
ssh staging
python manage.py migrate --check
python manage.py migrate

# 3. 프로덕션 백업
pg_dump style_license_db > backup_$(date +%Y%m%d).sql

# 4. 프로덕션 배포
ssh production
python manage.py migrate --check
python manage.py migrate

# 5. 검증
python manage.py showmigrations
python manage.py check
```

---

## 2. 성능 최적화

### 슬로우 쿼리 분석

```sql
-- pg_stat_statements 활성화 필요
SELECT 
    calls,
    total_exec_time,
    mean_exec_time,
    query
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- EXPLAIN ANALYZE
EXPLAIN ANALYZE
SELECT * FROM generations
WHERE is_public = true
ORDER BY created_at DESC
LIMIT 20;
```

### 인덱스 점검

```sql
-- 사용되지 않는 인덱스
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan as scans,
    pg_size_pretty(pg_relation_size(indexrelid)) as size
FROM pg_stat_user_indexes
WHERE idx_scan = 0
  AND schemaname = 'public'
ORDER BY pg_relation_size(indexrelid) DESC;

-- 인덱스 사용률
SELECT 
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
WHERE schemaname = 'public'
ORDER BY idx_scan ASC;
```

### 캐시 카운터 동기화

#### 트리거 방식
```sql
-- 좋아요 수 자동 업데이트
CREATE OR REPLACE FUNCTION update_like_count()
RETURNS TRIGGER AS $$
BEGIN
    IF TG_OP = 'INSERT' THEN
        UPDATE generations 
        SET like_count = like_count + 1 
        WHERE id = NEW.generation_id;
    ELSIF TG_OP = 'DELETE' THEN
        UPDATE generations 
        SET like_count = like_count - 1 
        WHERE id = OLD.generation_id;
    END IF;
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_like_count
AFTER INSERT OR DELETE ON likes
FOR EACH ROW EXECUTE FUNCTION update_like_count();
```

#### 배치 재계산 (Celery)
```python
@periodic_task(run_every=timedelta(hours=1))
def recalculate_counters():
    """좋아요/댓글 수 재계산"""
    from django.db.models import Count
    
    generations = Generation.objects.annotate(
        actual_likes=Count('likes'),
        actual_comments=Count('comments')
    ).filter(
        Q(like_count__ne=F('actual_likes')) |
        Q(comment_count__ne=F('actual_comments'))
    )
    
    for gen in generations:
        gen.like_count = gen.actual_likes
        gen.comment_count = gen.actual_comments
    
    Generation.objects.bulk_update(
        generations, 
        ['like_count', 'comment_count']
    )
```

### 커넥션 풀링

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'style_license_db',
        'CONN_MAX_AGE': 600,  # 10분 재사용
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'  # 30초
        },
    }
}
```

---

## 3. 백업 & 복구

### 정기 백업 스크립트

```bash
#!/bin/bash
# /usr/local/bin/daily_backup.sh

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/var/backups/postgresql"
DB_NAME="style_license_db"

# Full backup (압축)
pg_dump -U postgres -Fc $DB_NAME > $BACKUP_DIR/backup_$DATE.dump

# 7일 이상 된 백업 삭제
find $BACKUP_DIR -name "backup_*.dump" -mtime +7 -delete

echo "Backup completed: backup_$DATE.dump"
```

### Crontab 설정

```bash
# 매일 새벽 3시 백업
0 3 * * * /usr/local/bin/daily_backup.sh >> /var/log/backup.log 2>&1
```

### 복구

```bash
# 전체 복구
pg_restore -U postgres -d style_license_db -c backup_20250101.dump

# 특정 테이블만 복구
pg_restore -U postgres -d style_license_db -t users backup.dump

# SQL 파일 복구
psql -U postgres style_license_db < backup.sql
```

### AWS RDS 스냅샷

```bash
# 스냅샷 생성
aws rds create-db-snapshot \
    --db-instance-identifier style-license-db \
    --db-snapshot-identifier manual-snapshot-$(date +%Y%m%d)

# 스냅샷 목록
aws rds describe-db-snapshots \
    --db-instance-identifier style-license-db
```

---

## 4. 모니터링

### 테이블 크기 확인

```sql
-- 테이블별 크기
SELECT 
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 커넥션 모니터링

```sql
-- 현재 연결 수
SELECT count(*) FROM pg_stat_activity;

-- 활성 쿼리
SELECT 
    pid,
    usename,
    state,
    query_start,
    now() - query_start AS duration,
    query
FROM pg_stat_activity
WHERE state != 'idle'
ORDER BY duration DESC;

-- 긴 트랜잭션 (30초 이상)
SELECT 
    pid,
    now() - xact_start AS duration,
    state,
    query
FROM pg_stat_activity
WHERE xact_start IS NOT NULL
  AND now() - xact_start > interval '30 seconds';

-- 락 대기 중인 쿼리
SELECT 
    blocked.pid AS blocked_pid,
    blocked.query AS blocked_query,
    blocking.pid AS blocking_pid,
    blocking.query AS blocking_query
FROM pg_stat_activity blocked
JOIN pg_locks blocked_locks ON blocked.pid = blocked_locks.pid
JOIN pg_locks blocking_locks ON blocking_locks.locktype = blocked_locks.locktype
JOIN pg_stat_activity blocking ON blocking.pid = blocking_locks.pid
WHERE NOT blocked_locks.granted
  AND blocking_locks.granted;
```

### Django 쿼리 로깅

```python
# settings.py (개발 환경)
LOGGING = {
    'version': 1,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'loggers': {
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
        },
    },
}
```

### Prometheus + Grafana

```python
# pip install django-prometheus

# settings.py
INSTALLED_APPS = [
    'django_prometheus',
    # ...
]

MIDDLEWARE = [
    'django_prometheus.middleware.PrometheusBeforeMiddleware',
    # ...
    'django_prometheus.middleware.PrometheusAfterMiddleware',
]

DATABASES = {
    'default': {
        'ENGINE': 'django_prometheus.db.backends.postgresql',
        # ...
    }
}
```

---

## 5. 유지보수

### VACUUM

```sql
-- 자동 VACUUM 설정 확인
SHOW autovacuum;

-- 수동 VACUUM
VACUUM ANALYZE generations;

-- VACUUM FULL (테이블 재구성, 락 발생 주의)
VACUUM FULL generations;

-- VACUUM 통계
SELECT 
    relname,
    last_vacuum,
    last_autovacuum,
    n_dead_tup
FROM pg_stat_user_tables
WHERE schemaname = 'public'
ORDER BY n_dead_tup DESC;
```

### REINDEX

```sql
-- 인덱스 재구성
REINDEX TABLE generations;

-- CONCURRENT (락 없음)
REINDEX INDEX CONCURRENTLY idx_generations_user;
```

### 오래된 데이터 정리

```python
@periodic_task(run_every=timedelta(days=1))
def cleanup_old_data():
    """배치 데이터 정리"""
    
    # 30일 이상 된 읽은 알림 삭제
    cutoff = timezone.now() - timedelta(days=30)
    Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff
    ).delete()
    
    # 7일 이상 된 실패 생성 삭제
    cutoff = timezone.now() - timedelta(days=7)
    Generation.objects.filter(
        status='failed',
        created_at__lt=cutoff
    ).delete()
```

---

## 긴급 상황 대응

### DB 응답 없음
```bash
# 1. 락 확인
SELECT * FROM pg_locks WHERE NOT granted;

# 2. 긴 트랜잭션 확인
SELECT pid, now() - xact_start, query 
FROM pg_stat_activity 
WHERE xact_start IS NOT NULL;

# 3. 프로세스 종료 (주의!)
SELECT pg_terminate_backend(pid);
```

### 디스크 풀
```bash
# 1. 로그 삭제
find /var/log -name "*.log" -mtime +7 -delete

# 2. 오래된 백업 삭제
find /var/backups -name "*.dump" -mtime +30 -delete

# 3. VACUUM FULL
psql -U postgres -d style_license_db -c "VACUUM FULL;"
```

### 슬로우 다운
```bash
# 1. 슬로우 쿼리 확인
SELECT query, mean_exec_time 
FROM pg_stat_statements 
ORDER BY mean_exec_time DESC LIMIT 5;

# 2. 인덱스 추가
CREATE INDEX CONCURRENTLY idx_name ON table(column);

# 3. 통계 업데이트
ANALYZE;
```

---

## 체크리스트

### 일일 점검
- [ ] 백업 성공 여부
- [ ] 슬로우 쿼리 로그
- [ ] 디스크 사용량
- [ ] 에러 로그

### 주간 점검
- [ ] 테이블 크기 증가 추이
- [ ] 인덱스 사용률
- [ ] VACUUM 실행 여부
- [ ] 커넥션 풀 상태

### 월간 점검
- [ ] 쿼리 성능 분석
- [ ] REINDEX 실행
- [ ] 오래된 데이터 아카이빙
- [ ] 보안 패치

---

## 유용한 명령어

```bash
# PostgreSQL 상태
sudo systemctl status postgresql

# 재시작
sudo systemctl restart postgresql

# 로그 확인
sudo tail -f /var/log/postgresql/postgresql-15-main.log

# 데이터 디렉토리 크기
du -sh /var/lib/postgresql/15/main/

# psql 접속
sudo -u postgres psql style_license_db
```

---

[← 돌아가기](README.md) | [쿼리 예제 보기](QUERIES.md)