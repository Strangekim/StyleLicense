# QUERIES.md

실전 쿼리 패턴 및 Django ORM 예제

[← 돌아가기](README.md)

---

## 목차
1. [인증 & 사용자](#1-인증--사용자)
2. [토큰 거래](#2-토큰-거래)
3. [화풍 & 생성](#3-화풍--생성)
4. [소셜 기능](#4-소셜-기능)
5. [검색](#5-검색)
6. [성능 최적화](#6-성능-최적화)

---

## 1. 인증 & 사용자

### OAuth 로그인 (Google)

```python
from django.db import transaction

@transaction.atomic
def google_login(google_user_id, email, username, profile_image):
    """구글 로그인 처리"""
    user, created = User.objects.get_or_create(
        provider='google',
        provider_user_id=google_user_id,
        defaults={
            'username': username,
            'profile_image': profile_image,
        }
    )
    
    if created:
        # 가입 축하 토큰 100개 지급
        user.token_balance = 100
        user.save()
        
        Transaction.objects.create(
            sender_id=user.id,
            receiver_id=None,
            amount=100,
            status='completed',
            memo='Welcome bonus'
        )
    
    return user
```

### 작가 권한 부여

```python
@transaction.atomic
def upgrade_to_artist(user_id, artist_name):
    """사용자 → 작가 권한 부여"""
    user = User.objects.select_for_update().get(id=user_id)
    
    if user.role == 'artist':
        raise ValueError("이미 작가입니다")
    
    # 역할 변경
    user.role = 'artist'
    user.save()
    
    # 작가 프로필 생성
    artist = Artist.objects.create(
        user_id=user_id,
        artist_name=artist_name or user.username
    )
    
    return artist
```

---

## 2. 토큰 거래

### 토큰 구매 (토스 페이먼츠)

```python
@transaction.atomic
def complete_token_purchase(payment_key, order_id, amount_tokens, price_per_token, buyer_id):
    """토스 결제 완료 처리 (웹훅)"""
    
    # 멱등성 체크
    purchase = Purchase.objects.filter(
        provider_payment_key=payment_key
    ).first()
    
    if purchase and purchase.status == 'paid':
        return purchase  # 이미 처리됨
    
    # Purchase 생성 또는 업데이트
    if not purchase:
        purchase = Purchase.objects.create(
            buyer_id=buyer_id,
            amount_tokens=amount_tokens,
            price_per_token=price_per_token,
            provider='toss',
            provider_payment_key=payment_key,
            provider_order_id=order_id,
            status='pending'
        )
    
    # 결제 승인
    purchase.status = 'paid'
    purchase.approved_at = timezone.now()
    purchase.save()
    
    # 토큰 충전
    user = User.objects.select_for_update().get(id=buyer_id)
    user.token_balance += amount_tokens
    user.save()
    
    # 거래 기록
    Transaction.objects.create(
        sender_id=buyer_id,
        receiver_id=None,  # 플랫폼으로부터
        amount=amount_tokens,
        price_per_token=price_per_token,
        status='completed'
    )
    
    return purchase
```

### 이미지 생성 결제

```python
@transaction.atomic
def charge_for_generation(user_id, style_id, description, aspect_ratio='1:1'):
    """이미지 생성 토큰 차감"""
    
    # 락 걸고 조회
    user = User.objects.select_for_update().get(id=user_id)
    style = Style.objects.select_for_update().get(
        id=style_id,
        training_status='completed',
        is_active=True
    )
    
    cost = style.generation_cost_tokens
    
    # 잔액 확인
    if user.token_balance < cost:
        raise ValueError(f"토큰 부족 (필요: {cost}, 보유: {user.token_balance})")
    
    # 사용자 토큰 차감
    user.token_balance -= cost
    user.save()
    
    # 작가 수익 증가
    artist = Artist.objects.select_for_update().get(user_id=style.artist_id)
    artist.earned_token_balance += cost
    artist.save()
    
    # Generation 생성
    generation = Generation.objects.create(
        user_id=user_id,
        style_id=style_id,
        aspect_ratio=aspect_ratio,
        consumed_tokens=cost,
        description=description,
        status='queued'
    )
    
    # 거래 기록
    Transaction.objects.create(
        sender_id=user_id,
        receiver_id=style.artist_id,
        amount=cost,
        related_style_id=style_id,
        status='completed'
    )
    
    # RabbitMQ로 작업 전송
    send_generation_job(generation.id)
    
    return generation
```

### 환불 처리

```python
@transaction.atomic
def refund_generation(generation_id):
    """실패한 생성 환불"""
    generation = Generation.objects.select_for_update().get(id=generation_id)
    
    if generation.status != 'failed':
        raise ValueError("실패한 생성만 환불 가능")
    
    # 원본 거래 찾기
    original_tx = Transaction.objects.get(
        sender_id=generation.user_id,
        related_style_id=generation.style_id,
        status='completed'
    )
    
    # 환불 거래 생성 (역방향)
    refund_tx = Transaction.objects.create(
        sender_id=original_tx.receiver_id,
        receiver_id=original_tx.sender_id,
        amount=original_tx.amount,
        status='completed',
        memo=f'환불: generation #{generation_id}'
    )
    
    # 원본 거래 환불 표시
    original_tx.refunded = True
    original_tx.save()
    
    # 토큰 반환
    user = User.objects.select_for_update().get(id=generation.user_id)
    user.token_balance += generation.consumed_tokens
    user.save()
    
    # 작가 수익 차감
    artist = Artist.objects.select_for_update().get(user_id=original_tx.receiver_id)
    artist.earned_token_balance -= generation.consumed_tokens
    artist.save()
    
    return refund_tx
```

---

## 3. 화풍 & 생성

### 스타일 학습 요청

```python
@transaction.atomic
def request_style_training(artist_id, style_name, description, image_files):
    """스타일 학습 요청"""
    
    # MVP: 작가당 1개 제한
    existing_count = Style.objects.filter(artist_id=artist_id).count()
    if existing_count >= 1:
        raise ValueError("작가당 1개 스타일만 생성 가능합니다")
    
    # Style 생성
    style = Style.objects.create(
        artist_id=artist_id,
        name=style_name,
        description=description,
        training_status='pending',
        generation_cost_tokens=50
    )
    
    # 이미지 업로드
    artworks = []
    for image_file in image_files:
        s3_url = upload_to_s3(image_file)
        artworks.append(
            Artwork(
                style_id=style.id,
                image_url=s3_url,
                is_valid=False  # 검증 전
            )
        )
    
    Artwork.objects.bulk_create(artworks)
    
    # 검증 큐 전송
    send_validation_job(style.id)
    
    return style
```

### 생성 완료 처리 (Inference Server 콜백)

```python
@transaction.atomic
def complete_generation(generation_id, result_url):
    """이미지 생성 완료"""
    generation = Generation.objects.select_for_update().get(id=generation_id)
    
    generation.status = 'completed'
    generation.result_url = result_url
    generation.save()
    
    # 알림 전송
    Notification.objects.create(
        recipient_id=generation.user_id,
        actor_id=None,  # 시스템 알림
        type='generation_complete',
        target_type='generation',
        target_id=generation_id
    )
    
    return generation
```

### 공개 피드 조회 (Cursor Pagination)

```python
def get_public_feed(cursor=None, limit=20, user_id=None):
    """공개 생성물 피드"""
    
    queryset = Generation.objects.filter(
        is_public=True,
        status='completed'
    ).select_related('user', 'style').prefetch_related(
        'generation_tags__tag'
    )
    
    # Cursor-based pagination
    if cursor:
        queryset = queryset.filter(created_at__lt=cursor)
    
    # 좋아요 여부 표시
    if user_id:
        queryset = queryset.annotate(
            is_liked=Exists(
                Like.objects.filter(
                    generation_id=OuterRef('pk'),
                    user_id=user_id
                )
            )
        )
    
    generations = list(queryset.order_by('-created_at')[:limit])
    next_cursor = generations[-1].created_at if generations else None
    
    return {
        'results': generations,
        'next_cursor': next_cursor.isoformat() if next_cursor else None
    }
```

---

## 4. 소셜 기능

### 좋아요 토글

```python
@transaction.atomic
def toggle_like(user_id, generation_id):
    """좋아요 추가/제거"""
    
    like = Like.objects.filter(
        user_id=user_id,
        generation_id=generation_id
    ).first()
    
    if like:
        # 좋아요 취소
        like.delete()
        Generation.objects.filter(id=generation_id).update(
            like_count=F('like_count') - 1
        )
        return {'action': 'unliked', 'liked': False}
    else:
        # 좋아요 추가
        Like.objects.create(
            user_id=user_id,
            generation_id=generation_id
        )
        Generation.objects.filter(id=generation_id).update(
            like_count=F('like_count') + 1
        )
        
        # 알림 (자기 게시물 제외)
        generation = Generation.objects.get(id=generation_id)
        if generation.user_id != user_id:
            Notification.objects.create(
                recipient_id=generation.user_id,
                actor_id=user_id,
                type='like',
                target_type='generation',
                target_id=generation_id
            )
        
        return {'action': 'liked', 'liked': True}
```

### 댓글 작성

```python
@transaction.atomic
def create_comment(user_id, generation_id, content, parent_id=None):
    """댓글/대댓글 작성"""
    
    # 대댓글 깊이 제한 (MVP: 1단계)
    if parent_id:
        parent = Comment.objects.get(id=parent_id)
        if parent.parent_id is not None:
            raise ValueError("대댓글의 대댓글은 불가능합니다")
    
    # 댓글 생성
    comment = Comment.objects.create(
        user_id=user_id,
        generation_id=generation_id,
        content=content,
        parent_id=parent_id
    )
    
    # 카운트 증가
    Generation.objects.filter(id=generation_id).update(
        comment_count=F('comment_count') + 1
    )
    
    # 알림 생성
    generation = Generation.objects.get(id=generation_id)
    
    if parent_id and parent.user_id != user_id:
        # 부모 댓글 작성자에게
        Notification.objects.create(
            recipient_id=parent.user_id,
            actor_id=user_id,
            type='comment',
            target_type='comment',
            target_id=comment.id,
            metadata={'excerpt': content[:100]}
        )
    elif generation.user_id != user_id:
        # 게시물 작성자에게
        Notification.objects.create(
            recipient_id=generation.user_id,
            actor_id=user_id,
            type='comment',
            target_type='comment',
            target_id=comment.id,
            metadata={'excerpt': content[:100]}
        )
    
    return comment
```

### 팔로우/언팔로우

```python
@transaction.atomic
def toggle_follow(follower_id, following_id):
    """팔로우 토글"""
    
    if follower_id == following_id:
        raise ValueError("자기 자신을 팔로우할 수 없습니다")
    
    follow = Follow.objects.filter(
        follower_id=follower_id,
        following_id=following_id
    ).first()
    
    if follow:
        # 언팔로우
        follow.delete()
        return {'action': 'unfollowed', 'following': False}
    else:
        # 팔로우
        Follow.objects.create(
            follower_id=follower_id,
            following_id=following_id
        )
        
        # 알림
        Notification.objects.create(
            recipient_id=following_id,
            actor_id=follower_id,
            type='follow',
            target_type='user',
            target_id=follower_id
        )
        
        return {'action': 'followed', 'following': True}
```

---

## 5. 검색

### 태그로 검색

```python
def search_by_tags(tag_names, limit=20):
    """여러 태그로 생성물 검색 (OR)"""
    
    # 태그 이름으로 generation_id 찾기
    generation_ids = GenerationTag.objects.filter(
        tag__name__in=[t.lower() for t in tag_names]
    ).values_list('generation_id', flat=True).distinct()
    
    # 생성물 조회
    generations = Generation.objects.filter(
        id__in=generation_ids,
        is_public=True,
        status='completed'
    ).select_related('user', 'style').prefetch_related(
        'generation_tags__tag'
    ).order_by('-like_count')[:limit]
    
    return generations
```

### 스타일 검색

```python
def search_styles(query, limit=20):
    """스타일 이름/작가명 검색"""
    from django.db.models import Q, Count
    
    styles = Style.objects.filter(
        Q(name__icontains=query) | 
        Q(artist__artist_name__icontains=query) |
        Q(artist__user__username__icontains=query),
        is_active=True,
        is_flagged=False,
        training_status='completed'
    ).select_related('artist__user').annotate(
        usage_count=Count(
            'generations',
            filter=Q(generations__status='completed')
        )
    ).order_by('-follower_count')[:limit]
    
    return styles
```

---

## 6. 성능 최적화

### N+1 쿼리 방지

```python
# ❌ Bad: N+1 쿼리
generations = Generation.objects.all()
for gen in generations:
    print(gen.user.username)  # 각각 쿼리
    print(gen.style.name)     # 각각 쿼리

# ✅ Good: select_related (1:1, N:1)
generations = Generation.objects.select_related('user', 'style').all()

# ✅ Good: prefetch_related (N:M)
generations = Generation.objects.prefetch_related(
    'generation_tags__tag',
    'likes',
    'comments__user'
).all()
```

### 필요한 컬럼만 조회

```python
# only() - 지정한 컬럼만
users = User.objects.only('id', 'username', 'profile_image')

# defer() - 특정 컬럼 제외
users = User.objects.defer('bio')  # bio 제외
```

### Bulk 연산

```python
# ❌ Bad
for tag_name in tag_names:
    tag = Tag.objects.create(name=tag_name)

# ✅ Good
tags = [Tag(name=name) for name in tag_names]
Tag.objects.bulk_create(tags, ignore_conflicts=True)

# Bulk update
generations = Generation.objects.filter(user_id=user_id)
for gen in generations:
    gen.is_public = False
Generation.objects.bulk_update(generations, ['is_public'])
```

### 인덱스 활용 쿼리

```python
# ✅ 인덱스 사용: idx_generations_public
Generation.objects.filter(
    is_public=True
).order_by('-created_at')

# ❌ 인덱스 미사용: LIKE 연산
Generation.objects.filter(description__contains='test')

# ✅ Full-text search (PostgreSQL)
from django.contrib.postgres.search import SearchVector

Generation.objects.annotate(
    search=SearchVector('description')
).filter(search='sunset portrait')
```

### 통계 쿼리 최적화

```python
from django.db.models import Count, Sum, Avg, Q

# 사용자 통계 (한 번에)
user_stats = User.objects.filter(id=user_id).annotate(
    total_generations=Count('generations'),
    public_generations=Count('generations', filter=Q(generations__is_public=True)),
    total_likes=Sum('generations__like_count'),
    follower_count=Count('follower_set'),
    following_count=Count('following_set')
).first()
```

---

## 자주 사용하는 SQL 패턴

### 토큰 잔액 재계산

```sql
-- 사용자별 실제 잔액 계산
WITH received AS (
    SELECT receiver_id, SUM(amount) as total
    FROM transactions
    WHERE status = 'completed' AND refunded = false
    GROUP BY receiver_id
),
sent AS (
    SELECT sender_id, SUM(amount) as total
    FROM transactions
    WHERE status = 'completed' AND refunded = false
    GROUP BY sender_id
)
SELECT 
    u.id,
    u.username,
    u.token_balance as stored_balance,
    COALESCE(r.total, 0) - COALESCE(s.total, 0) as actual_balance
FROM users u
LEFT JOIN received r ON u.id = r.receiver_id
LEFT JOIN sent s ON u.id = s.sender_id
WHERE u.token_balance != COALESCE(r.total, 0) - COALESCE(s.total, 0);
```

### 인기 스타일 (기간별)

```sql
-- 최근 7일 인기 스타일
SELECT 
    s.id,
    s.name,
    COUNT(g.id) as recent_usage,
    SUM(g.like_count) as total_likes
FROM styles s
LEFT JOIN generations g ON s.id = g.style_id
WHERE g.status = 'completed'
  AND g.created_at >= NOW() - INTERVAL '7 days'
GROUP BY s.id, s.name
ORDER BY recent_usage DESC, total_likes DESC
LIMIT 10;
```

---

[← 돌아가기](README.md) | [운영 가이드 보기](OPERATIONS.md)