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

## 3. 백업 & 복구 (Cloud SQL)

**운영 환경: Google Cloud SQL for PostgreSQL**

Cloud SQL은 완전 관리형 서비스이므로, 백업 및 복구가 매우 간단하며 자동화됩니다. EC2에서처럼 `pg_dump`를 수동으로 실행하고 Cron을 설정할 필요가 없습니다.

### 3.1 자동 백업
- **정책**: Cloud SQL은 하루에 한 번 지정된 시간에 모든 데이터베이스를 자동으로 백업합니다.
- **보관**: 최근 7개의 자동 백업이 기본적으로 보관되며, 최대 365일까지 보관 기간을 설정할 수 있습니다.
- **설정**: GCP 콘솔의 Cloud SQL 인스턴스 설정에서 백업 시간과 보관 주기를 설정할 수 있습니다.

### 3.2 특정 시점 복구 (Point-in-Time Recovery, PITR)
- **기능**: PITR을 활성화하면, 마지막 자동 백업 이후 특정 시점(분 단위)으로 데이터베이스를 복구할 수 있습니다. 트랜잭션 로그(WAL)를 사용하여 정밀한 복구를 지원합니다.
- **요구사항**: PITR을 사용하려면 자동 백업이 활성화되어 있어야 합니다.
- **복구 방법**: GCP 콘솔에서 복구하려는 인스턴스를 선택하고 '복제' 또는 '복원' 옵션을 통해 특정 시점을 지정하면, 해당 시점의 데이터를 가진 새로운 인스턴스가 생성됩니다.

### 3.3 수동 백업 (On-Demand)
- **필요성**: 배포 직전이나 중요한 데이터 변경 작업 전에 안전장치로 수동 백업을 생성할 수 있습니다.
- **방법**: GCP 콘솔 또는 `gcloud` CLI 명령어를 통해 언제든지 현재 상태의 백업을 생성할 수 있습니다.
```bash
# gcloud를 사용한 수동 백업 생성
gcloud sql backups create --instance=[INSTANCE_NAME] --description="Pre-deployment backup"
```

### 3.4 데이터 내보내기 (Export)
- **용도**: 다른 PostgreSQL 데이터베이스로 데이터를 이전하거나, 특정 형식(SQL, CSV)으로 데이터를 내보낼 때 사용합니다.
- **방법**: Cloud Storage 버킷을 지정하여 `pg_dump` 형식의 SQL 파일 또는 CSV 파일로 내보낼 수 있습니다.
```bash
# 특정 데이터베이스를 SQL 형식으로 Cloud Storage에 내보내기
gcloud sql export sql [INSTANCE_NAME] gs://[BUCKET_NAME]/sqldump.sql --database=[DATABASE_NAME]
```

---

## 4. 모니터링 (Cloud SQL)

Cloud SQL은 Google Cloud의 모니터링 서비스와 완벽하게 통합되어 있어, 별도의 모니터링 에이전트 설치 없이도 상세한 지표를 확인할 수 있습니다.

### 4.1 Cloud SQL 대시보드
- GCP 콘솔의 Cloud SQL 페이지에서 각 인스턴스에 대한 핵심 성능 지표를 실시간으로 확인할 수 있습니다.
- **주요 모니터링 항목**:
  - CPU 사용률
  - 메모리 사용률
  - 스토리지 사용률
  - 활성 연결 수 (Active Connections)
  - 읽기/쓰기 작업 수 (IOPS)
  - 트랜잭션 처리량

### 4.2 Cloud Monitoring (구 Stackdriver)
- **기능**: 더 상세한 측정항목을 보고, 특정 조건에 대한 알림(Alerting)을 설정할 수 있습니다.
- **알림 정책 예시**:
  - CPU 사용률이 10분 동안 80% 이상일 경우 이메일 알림
  - 사용 가능한 스토리지가 10% 미만일 경우 Slack 알림
  - 활성 연결 수가 100개를 초과할 경우 PagerDuty 알림

### 4.3 슬로우 쿼리 분석
- **기능**: Cloud SQL은 `pg_stat_statements` 확장을 지원하며, 쿼리 실행 통계를 Cloud Logging으로 전송하도록 설정할 수 있습니다.
- **설정**: 데이터베이스 플래그 `cloudsql.enable_pg_stat_statements`를 `on`으로 설정합니다.
- **분석**: Cloud Logging에서 `logName="projects/[PROJECT_ID]/logs/cloudsql.googleapis.com%2Fpostgres.log"` 필터를 사용하여 실행 시간이 오래 걸리는 쿼리를 식별하고 분석할 수 있습니다.

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