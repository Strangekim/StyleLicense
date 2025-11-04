# Backend Code Guide

**목적**: Django REST Framework 기반 Backend 개발 시 따라야 할 코드 패턴, 규칙, 예제를 제공합니다.

**대상**: Backend 개발자, 코드 리뷰어

---

## 목차
1. [코드 작성 원칙](#1-코드-작성-원칙)
2. [Model 패턴](#2-model-패턴)
3. [Serializer 패턴](#3-serializer-패턴)
4. [ViewSet 패턴](#4-viewset-패턴)
5. [Service Layer 패턴](#5-service-layer-패턴)
6. [RabbitMQ 패턴](#6-rabbitmq-패턴)
7. [Permission 패턴](#7-permission-패턴)
8. [에러 처리](#8-에러-처리)
9. [성능 최적화](#9-성능-최적화)
10. [테스트 작성](#10-테스트-작성)

---

## 1. 코드 작성 원칙

### 1.1 Django REST Framework 철학

- **Serializers는 데이터 변환만** - 비즈니스 로직 금지
- **Views는 HTTP 요청/응답만** - 비즈니스 로직 금지
- **Services에 비즈니스 로직** - 재사용 가능한 단위
- **Models는 데이터 구조** - 복잡한 로직 금지

### 1.2 네이밍 규칙

```python
# Models: 단수형 PascalCase
class StyleModel(models.Model):
    pass

# Serializers: {ModelName}Serializer
class StyleModelSerializer(serializers.ModelSerializer):
    pass

# ViewSets: {ModelName}ViewSet
class StyleViewSet(viewsets.ModelViewSet):
    pass

# Services: {Domain}Service
class TokenService:
    pass

# Functions: snake_case, 동사로 시작
def consume_tokens(user_id, amount):
    pass
```

### 1.3 Import 순서

```python
# 1. Standard library
import json
import uuid
from datetime import datetime

# 2. Django core
from django.db import models, transaction
from django.conf import settings

# 3. Third-party
from rest_framework import viewsets, serializers
import pika

# 4. Local
from app.models import User, StyleModel
from app.services import token_service
```

---

## 2. Model 패턴

### 2.1 기본 Model 구조

```python
# app/models/style.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class StyleModel(models.Model):
    """작가의 화풍을 나타내는 AI 모델"""

    # Training status choices
    TRAINING_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('training', 'Training'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]

    # Fields
    artist = models.ForeignKey(
        User,
        on_delete=models.RESTRICT,  # 작가 삭제 제한
        related_name='styles'
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    training_status = models.CharField(
        max_length=20,
        choices=TRAINING_STATUS_CHOICES,
        default='pending',
        db_index=True  # 자주 필터링
    )
    generation_cost_tokens = models.IntegerField(default=100)  # 토큰 단위
    model_path = models.TextField(blank=True, null=True)  # S3 경로

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'styles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['training_status', 'artist']),  # 복합 인덱스
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.name} by {self.artist.username}"

    def is_ready(self):
        """생성에 사용 가능한 상태인지 확인"""
        return self.training_status == 'completed' and self.model_path
```

### 2.2 Related Names 규칙

```python
# Foreign Key: 복수형
class GeneratedImage(models.Model):
    style = models.ForeignKey(
        StyleModel,
        on_delete=models.RESTRICT,
        related_name='generated_images'  # style.generated_images.all()
    )
    
# Many-to-Many: 복수형
class CommunityPost(models.Model):
    liked_by = models.ManyToManyField(
        User,
        through='PostLike',
        related_name='liked_posts'  # user.liked_posts.all()
    )
```

### 2.3 Custom Model Methods

```python
class TokenTransaction(models.Model):
    # ... fields ...
    
    @classmethod
    def get_user_balance(cls, user):
        """사용자의 현재 토큰 잔액 계산"""
        transactions = cls.objects.filter(user=user)
        balance = sum(t.amount for t in transactions)
        return balance
    
    def is_refundable(self):
        """
        환불 가능 여부 확인

        Note: transaction_type은 DB 컬럼이 아닌 Serializer에서 동적 계산하는 필드입니다.
        실제 구현 시에는 sender_id, receiver_id, related_generation_id 조합으로 판별합니다.
        """
        # 이미지 생성 결제 건만 환불 가능
        is_generation_payment = (
            self.sender_id is not None and
            self.receiver_id is not None and
            self.related_generation_id is not None
        )
        return (
            is_generation_payment and
            (datetime.now() - self.created_at).days < 7
        )
```

---

## 3. Serializer 패턴

### 3.1 ModelSerializer 기본

```python
# app/serializers/style.py
from rest_framework import serializers
from app.models import StyleModel

class StyleModelSerializer(serializers.ModelSerializer):
    # Read-only 필드
    artist_name = serializers.CharField(
        source='artist.username',
        read_only=True
    )
    
    # Write-only 필드
    training_images = serializers.ListField(
        child=serializers.ImageField(),
        write_only=True
    )
    
    class Meta:
        model = StyleModel
        fields = [
            'id',
            'name',
            'description',
            'training_status',
            'generation_cost_tokens',
            'artist_name',  # read-only
            'training_images',  # write-only
            'created_at',
        ]
        read_only_fields = ['id', 'training_status', 'created_at']

    def validate_generation_cost_tokens(self, value):
        """가격 검증"""
        if value < 10:
            raise serializers.ValidationError(
                "Price must be at least 10 tokens"
            )
        if value > 10000:
            raise serializers.ValidationError(
                "Price cannot exceed 10,000 tokens"
            )
        return value
    
    def validate(self, attrs):
        """전체 데이터 검증"""
        training_images = attrs.get('training_images', [])
        if len(training_images) < 10:
            raise serializers.ValidationError({
                'training_images': 'At least 10 images required'
            })
        if len(training_images) > 100:
            raise serializers.ValidationError({
                'training_images': 'Maximum 100 images allowed'
            })
        return attrs
```

### 3.2 Nested Serializers

```python
# Read-only nested (depth 사용 금지, 명시적 serializer 사용)
class TrainingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingImage
        fields = ['id', 'image_url', 'tags']

class StyleModelDetailSerializer(serializers.ModelSerializer):
    training_images = TrainingImageSerializer(many=True, read_only=True)

    class Meta:
        model = StyleModel
        fields = ['id', 'name', 'training_status', 'training_images', 'created_at']
```

### 3.3 Writable Nested Serializers

```python
class CommentCreateSerializer(serializers.ModelSerializer):
    # 답글 작성 시 parent_id만 받음
    parent_id = serializers.IntegerField(required=False, allow_null=True)
    
    class Meta:
        model = Comment
        fields = ['content', 'parent_id']
    
    def create(self, validated_data):
        parent_id = validated_data.pop('parent_id', None)
        
        comment = Comment.objects.create(
            post=self.context['post'],
            author=self.context['request'].user,
            **validated_data
        )
        
        if parent_id:
            parent = Comment.objects.get(id=parent_id)
            comment.parent = parent
            comment.save()
        
        return comment
```

### 3.4 Dynamic Fields

```python
class DynamicFieldsModelSerializer(serializers.ModelSerializer):
    """클라이언트가 필요한 필드만 요청 가능"""
    
    def __init__(self, *args, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(*args, **kwargs)
        
        if fields is not None:
            allowed = set(fields)
            existing = set(self.fields)
            for field_name in existing - allowed:
                self.fields.pop(field_name)

# Usage: GET /api/styles/?fields=id,name,generation_cost_tokens
class StyleModelSerializer(DynamicFieldsModelSerializer):
    class Meta:
        model = StyleModel
        fields = '__all__'
```

---

## 4. ViewSet 패턴

### 4.1 ModelViewSet 기본

```python
# app/views/style.py
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from app.models import StyleModel
from app.serializers import StyleModelSerializer
from app.permissions import IsArtist
from app.services import rabbitmq_service, token_service

class StyleViewSet(viewsets.ModelViewSet):
    """스타일 CRUD 및 학습 요청"""
    
    queryset = StyleModel.objects.all()
    serializer_class = StyleModelSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        """사용자별 필터링"""
        queryset = super().get_queryset()

        # 작가는 자신의 스타일 전체 조회
        if self.request.user.role == 'artist':
            return queryset.filter(artist=self.request.user)

        # 일반 사용자는 완료된 스타일만 조회
        return queryset.filter(training_status='completed')
    
    def get_permissions(self):
        """Action별 권한 설정"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsArtist()]
        return super().get_permissions()
    
    def perform_create(self, serializer):
        """생성 시 artist 자동 할당"""
        serializer.save(artist=self.request.user)
    
    @action(detail=True, methods=['post'], permission_classes=[IsArtist])
    def train(self, request, pk=None):
        """학습 시작 커스텀 액션"""
        style = self.get_object()

        # 이미 학습 중이면 거부
        if style.training_status == 'training':
            return Response(
                {'error': 'Training already in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 학습 비용 차감 (100 토큰)
        if not token_service.consume_tokens(
            user_id=request.user.id,
            amount=100,
            reason=f'Training style {pk}'
        ):
            return Response(
                {'error': 'Insufficient tokens'},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        
        # RabbitMQ에 학습 작업 전송
        rabbitmq_service.publish_training_task(
            style_id=pk,
            image_urls=style.get_training_image_urls(),
            params={'epochs': 200, 'learning_rate': 1e-4}
        )

        # 상태 업데이트
        style.training_status = 'training'
        style.save()

        return Response({
            'message': 'Training started',
            'style_id': pk,
            'training_status': 'training'
        })
```

### 4.2 Custom Action 패턴

```python
class GenerationViewSet(viewsets.ModelViewSet):
    
    @action(detail=True, methods=['get'])
    def progress(self, request, pk=None):
        """생성 진행률 조회 (폴링용)"""
        generation = self.get_object()
        return Response({
            'status': generation.status,  # generations 테이블은 'status' 사용
            'progress': generation.progress_percent,
            'estimated_time_remaining': generation.estimated_seconds,
        })
    
    @action(detail=False, methods=['get'])
    def my_generations(self, request):
        """내 생성 이력 조회"""
        generations = GeneratedImage.objects.filter(
            user=request.user
        ).select_related('style')
        
        page = self.paginate_queryset(generations)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)
    
    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """생성 실패 시 재시도"""
        generation = self.get_object()
        
        if generation.status != 'FAILED':
            return Response(
                {'error': 'Only failed generations can be retried'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # 재시도 로직...
        return Response({'message': 'Retry queued'})
```

### 4.3 ViewSet Introspection

```python
class StyleViewSet(viewsets.ModelViewSet):
    
    def get_permissions(self):
        """Action에 따라 동적으로 권한 설정"""
        if self.action == 'list':
            permission_classes = [AllowAny]
        elif self.action in ['retrieve']:
            permission_classes = [IsAuthenticatedOrReadOnly]
        elif self.action in ['create', 'update', 'partial_update', 'destroy']:
            permission_classes = [IsArtist]
        else:  # custom actions
            permission_classes = [IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_serializer_class(self):
        """Action에 따라 다른 serializer 사용"""
        if self.action == 'list':
            return StyleModelListSerializer  # 간단한 필드만
        elif self.action == 'retrieve':
            return StyleModelDetailSerializer  # 모든 필드
        return StyleModelSerializer  # 기본
```

---

## 5. Service Layer 패턴

### 5.1 Service 기본 구조

```python
# app/services/token_service.py
from django.db import transaction
from app.models import User, TokenTransaction

class TokenService:
    """토큰 관련 비즈니스 로직"""
    
    @staticmethod
    @transaction.atomic
    def consume_tokens(user_id: int, amount: int, reason: str) -> bool:
        """
        토큰을 원자적으로 차감합니다.
        
        Args:
            user_id: 사용자 ID
            amount: 차감할 토큰 양
            reason: 차감 사유
            
        Returns:
            성공 여부
            
        Raises:
            User.DoesNotExist: 사용자가 존재하지 않음
        """
        # SELECT FOR UPDATE로 동시성 문제 방지
        user = User.objects.select_for_update().get(id=user_id)
        
        # 잔액 확인
        if user.token_balance < amount:
            return False
        
        # 차감
        user.token_balance -= amount
        user.save()

        # 거래 기록
        # Note: transaction_type 컬럼은 DB에 없으며,
        # sender_id/receiver_id/related_generation_id 조합으로 유형을 판별합니다.
        TokenTransaction.objects.create(
            sender_id=user_id,
            receiver_id=None,  # 플랫폼으로 지급
            amount=amount,
            memo=reason
        )

        return True
    
    @staticmethod
    @transaction.atomic
    def refund_tokens(user_id: int, amount: int, reason: str):
        """토큰 환불"""
        user = User.objects.select_for_update().get(id=user_id)
        
        user.token_balance += amount
        user.save()

        # 환불 거래 기록
        TokenTransaction.objects.create(
            sender_id=None,  # 플랫폼에서 발행
            receiver_id=user_id,
            amount=amount,
            memo=reason,
            refunded=True
        )
```

### 5.2 Service 호출 패턴

```python
# app/views/generation.py
from app.services import TokenService, RabbitMQService, NotificationService

class GenerationViewSet(viewsets.ModelViewSet):
    
    def create(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        style_id = serializer.validated_data['style_id']
        style = StyleModel.objects.get(id=style_id)
        cost = style.generation_cost_tokens

        # 1. 토큰 차감 (Service)
        token_service = TokenService()
        if not token_service.consume_tokens(
            user_id=request.user.id,
            amount=cost,
            reason=f'Image generation with style {style_id}'
        ):
            return Response(
                {'error': 'Insufficient tokens'},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )
        
        # 2. 생성 요청 저장
        generation = serializer.save(user=request.user, style=style)
        
        # 3. RabbitMQ에 작업 전송 (Service)
        rabbitmq_service = RabbitMQService()
        try:
            rabbitmq_service.publish_generation_task(
                generation_id=generation.id,
                style_id=style_id,
                prompt=serializer.validated_data['prompt'],
                params={'size': '512x512', 'steps': 50}
            )
        except Exception as e:
            # 실패 시 토큰 환불
            token_service.refund_tokens(
                user_id=request.user.id,
                amount=cost,
                reason=f'Generation failed: {str(e)}'
            )
            generation.delete()
            raise
        
        return Response(
            self.get_serializer(generation).data,
            status=status.HTTP_201_CREATED
        )
```

---

## 6. RabbitMQ 패턴

### 6.1 Publisher (Backend → AI Server)

```python
# app/services/rabbitmq_service.py
import pika
import json
import uuid
from django.conf import settings

class RabbitMQService:
    """RabbitMQ 메시지 발행"""
    
    def __init__(self):
        self.connection = pika.BlockingConnection(
            pika.ConnectionParameters(
                host=settings.RABBITMQ_HOST,
                port=settings.RABBITMQ_PORT,
                credentials=pika.PlainCredentials(
                    settings.RABBITMQ_USER,
                    settings.RABBITMQ_PASS
                )
            )
        )
        self.channel = self.connection.channel()
    
    def publish_training_task(self, style_id, image_urls, params):
        """학습 작업 발행"""
        queue_name = 'model_training'
        self.channel.queue_declare(queue=queue_name, durable=True)
        
        message = {
            'task_id': str(uuid.uuid4()),
            'type': 'model_training',
            'data': {
                'style_id': style_id,
                'images': image_urls,
                'parameters': params
            },
            'callback_url': (
                f'{settings.API_BASE_URL}'
                f'/api/webhooks/training/complete'
            )
        }
        
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,  # persistent
                content_type='application/json'
            )
        )
    
    def publish_generation_task(self, generation_id, style_id, prompt, params):
        """이미지 생성 작업 발행"""
        queue_name = 'image_generation'
        self.channel.queue_declare(queue=queue_name, durable=True)
        
        message = {
            'task_id': str(uuid.uuid4()),
            'type': 'image_generation',
            'data': {
                'generation_id': generation_id,
                'style_id': style_id,
                'prompt': prompt,
                'parameters': params
            },
            'callback_url': (
                f'{settings.API_BASE_URL}'
                f'/api/webhooks/generation/complete'
            )
        }
        
        self.channel.basic_publish(
            exchange='',
            routing_key=queue_name,
            body=json.dumps(message),
            properties=pika.BasicProperties(
                delivery_mode=2,
                content_type='application/json'
            )
        )
    
    def __del__(self):
        if hasattr(self, 'connection') and self.connection:
            self.connection.close()
```

### 6.2 Webhook Receiver (AI Server → Backend)

```python
# app/views/webhook.py
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.views.decorators.csrf import csrf_exempt

from app.models import StyleModel, GeneratedImage
from app.services import NotificationService

@csrf_exempt  # CSRF 제외 (INTERNAL_API_TOKEN으로 인증)
@api_view(['PATCH'])
@permission_classes([AllowAny])  # Middleware에서 인증
def training_progress(request, style_id):
    """학습 진행률 업데이트"""
    style = StyleModel.objects.get(id=style_id)
    
    progress = request.data.get('progress', 0)
    current_epoch = request.data.get('current_epoch')
    total_epochs = request.data.get('total_epochs')
    
    style.training_progress = progress
    style.training_current_epoch = current_epoch
    style.training_total_epochs = total_epochs
    style.save()
    
    return Response({'status': 'ok'})

@csrf_exempt
@api_view(['POST'])
@permission_classes([AllowAny])
def training_complete(request):
    """학습 완료 알림"""
    style_id = request.data.get('style_id')
    model_path = request.data.get('model_path')  # S3 URL
    success = request.data.get('success', True)
    error_message = request.data.get('error')
    
    style = StyleModel.objects.get(id=style_id)
    
    if success:
        style.training_status = 'completed'
        style.model_path = model_path
        notification_type = 'TRAINING_SUCCESS'
    else:
        style.training_status = 'failed'
        notification_type = 'TRAINING_FAILED'
    
    style.save()
    
    # 작가에게 알림
    NotificationService.create_notification(
        user_id=style.artist_id,
        type=notification_type,
        data={
            'style_id': style_id,
            'style_name': style.name,
            'error': error_message
        }
    )
    
    return Response({'status': 'ok'})
```

### 6.3 Webhook Authentication Middleware

```python
# app/middleware/webhook_auth.py
from django.http import JsonResponse
from django.conf import settings

class WebhookAuthMiddleware:
    """AI 서버 Webhook 인증 미들웨어"""
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Webhook 경로만 검증
        if request.path.startswith('/api/webhooks/'):
            # Authorization: Bearer <TOKEN> 파싱
            auth_header = request.headers.get('Authorization', '')
            if not auth_header.startswith('Bearer '):
                return JsonResponse(
                    {'error': 'Unauthorized'},
                    status=401
                )

            token = auth_header.replace('Bearer ', '')
            if token != settings.INTERNAL_API_TOKEN:
                return JsonResponse(
                    {'error': 'Unauthorized'},
                    status=401
                )

        return self.get_response(request)
```

---

## 7. Permission 패턴

### 7.1 Custom Permissions

```python
# app/permissions/custom.py
from rest_framework import permissions

class IsArtist(permissions.BasePermission):
    """작가 권한 확인"""
    
    message = "Only artists can perform this action."
    
    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'artist'
        )

class IsOwnerOrReadOnly(permissions.BasePermission):
    """소유자만 수정 가능, 읽기는 모두 가능"""
    
    def has_object_permission(self, request, view, obj):
        # 읽기 권한은 모두 허용
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 쓰기 권한은 소유자만
        return obj.artist == request.user

class IsOwner(permissions.BasePermission):
    """소유자만 접근 가능"""
    
    def has_object_permission(self, request, view, obj):
        # obj.user 또는 obj.artist 속성 사용
        owner = getattr(obj, 'user', getattr(obj, 'artist', None))
        return owner == request.user
```

### 7.2 Permission 조합

```python
class StyleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsArtist]  # AND 조건
    
    def get_permissions(self):
        """Action별 다른 권한"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()
```

---

## 8. 에러 처리

### 8.1 표준 에러 응답 형식

```python
# app/exceptions.py
from rest_framework.exceptions import APIException
from rest_framework import status

class InsufficientTokensError(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = '토큰이 부족합니다.'
    default_code = 'insufficient_tokens'

class TrainingInProgressError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = '이미 학습이 진행 중입니다.'
    default_code = 'training_in_progress'

# Usage
from app.exceptions import InsufficientTokensError

def some_view(request):
    if not has_enough_tokens:
        raise InsufficientTokensError(
            detail={'required': 100, 'current': 50}
        )
```

### 8.2 Global Exception Handler

```python
# config/settings/base.py
REST_FRAMEWORK = {
    'EXCEPTION_HANDLER': 'app.utils.exception_handler.custom_exception_handler',
}

# app/utils/exception_handler.py
from rest_framework.views import exception_handler
from rest_framework.response import Response

def custom_exception_handler(exc, context):
    """커스텀 에러 응답 형식"""
    response = exception_handler(exc, context)
    
    if response is not None:
        # 표준 형식으로 변환
        custom_response_data = {
            'error': {
                'code': getattr(exc, 'default_code', 'error'),
                'message': str(exc.detail),
                'details': exc.detail if isinstance(exc.detail, dict) else None
            }
        }
        response.data = custom_response_data
    
    return response
```

---

## 9. 성능 최적화

### 9.1 N+1 Query 방지

```python
# Bad: N+1 queries
class StyleViewSet(viewsets.ModelViewSet):
    def list(self, request):
        styles = StyleModel.objects.all()
        for style in styles:
            print(style.artist.username)  # 각 반복마다 쿼리

# Good: select_related (ForeignKey, OneToOne)
class StyleViewSet(viewsets.ModelViewSet):
    queryset = StyleModel.objects.select_related('artist')
    
# Good: prefetch_related (ManyToMany, Reverse ForeignKey)
class CommunityPostViewSet(viewsets.ModelViewSet):
    queryset = CommunityPost.objects.prefetch_related(
        'liked_by',  # ManyToMany
        'comments'   # Reverse ForeignKey
    )

# Advanced: Prefetch with filtering
from django.db.models import Prefetch

class StyleViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return StyleModel.objects.prefetch_related(
            Prefetch(
                'generated_images',
                queryset=GeneratedImage.objects.filter(is_public=True)
            )
        )
```

### 9.2 Database Indexing

```python
class StyleModel(models.Model):
    training_status = models.CharField(
        max_length=20,
        db_index=True  # 단일 컬럼 인덱스
    )

    class Meta:
        indexes = [
            # 복합 인덱스 (training_status + artist)
            models.Index(fields=['training_status', 'artist']),
            
            # 정렬용 인덱스
            models.Index(fields=['-created_at']),
            
            # 검색용 인덱스 (PostgreSQL)
            models.Index(
                fields=['name'],
                name='style_name_idx',
                opclasses=['varchar_pattern_ops']  # LIKE 검색
            ),
        ]
```

### 9.3 Caching

```python
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class StyleViewSet(viewsets.ModelViewSet):
    
    @method_decorator(cache_page(60 * 5))  # 5분 캐싱
    def list(self, request):
        return super().list(request)
    
    def get_queryset(self):
        # 캐시 키
        cache_key = f'popular_styles_{self.request.user.id}'
        
        # 캐시 확인
        cached = cache.get(cache_key)
        if cached:
            return cached
        
        # DB 조회
        queryset = StyleModel.objects.filter(
            training_status='completed'
        ).order_by('-view_count')[:10]
        
        # 캐시 저장 (5분)
        cache.set(cache_key, queryset, timeout=300)
        
        return queryset
```

### 9.4 Queryset Optimization

```python
class GenerationViewSet(viewsets.ModelViewSet):
    def get_queryset(self):
        return GeneratedImage.objects.select_related(
            'user',
            'style',
            'style__artist'  # 중첩 관계
        ).prefetch_related(
            'likes',
            'comments__author'  # 중첩 관계
        ).only(  # 필요한 필드만
            'id',
            'image_url',
            'prompt',
            'created_at',
            'user__username',
            'style__name'
        )
```

---

## 10. 테스트 작성

### 10.1 Pytest Fixtures

```python
# app/tests/conftest.py
import pytest
from app.models import User, StyleModel, TokenTransaction

@pytest.fixture
def user(db):
    """일반 사용자"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='password123',
        token_balance=1000
    )

@pytest.fixture
def artist(db):
    """작가 사용자"""
    return User.objects.create_user(
        username='artist',
        email='artist@example.com',
        password='password123',
        role='artist',
        token_balance=5000
    )

@pytest.fixture
def style_model(db, artist):
    """완료된 스타일 모델"""
    return StyleModel.objects.create(
        artist=artist,
        name='Test Style',
        description='Test description',
        training_status='completed',
        generation_cost_tokens=100,
        model_path='s3://stylelicense-models/test.safetensors'
    )

@pytest.fixture
def api_client():
    """DRF API 클라이언트"""
    from rest_framework.test import APIClient
    return APIClient()
```

### 10.2 Unit Tests (Service)

```python
# app/tests/test_token_service.py
import pytest
from app.services.token_service import TokenService

@pytest.mark.django_db
class TestTokenService:
    
    def test_consume_tokens_success(self, user):
        """토큰 소비 성공"""
        initial_balance = user.token_balance
        
        result = TokenService.consume_tokens(
            user_id=user.id,
            amount=100,
            reason='Test'
        )
        
        assert result is True
        
        user.refresh_from_db()
        assert user.token_balance == initial_balance - 100
    
    def test_consume_tokens_insufficient(self, user):
        """토큰 부족 시 실패"""
        result = TokenService.consume_tokens(
            user_id=user.id,
            amount=2000,  # 잔액보다 많음
            reason='Test'
        )
        
        assert result is False
        
        user.refresh_from_db()
        assert user.token_balance == 1000  # 변경 없음
    
    @pytest.mark.django_db(transaction=True)
    def test_consume_tokens_concurrency(self, user):
        """동시성 테스트"""
        from concurrent.futures import ThreadPoolExecutor
        
        def consume():
            return TokenService.consume_tokens(
                user_id=user.id,
                amount=100,
                reason='Concurrent test'
            )
        
        # 10개 동시 요청
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: consume(), range(10)))
        
        # 10번 성공해야 함
        assert sum(results) == 10
        
        user.refresh_from_db()
        assert user.token_balance == 0
```

### 10.3 Integration Tests (API)

```python
# app/tests/test_style_api.py
import pytest
from rest_framework import status

@pytest.mark.django_db
class TestStyleAPI:
    
    def test_list_styles(self, api_client, style_model):
        """스타일 목록 조회"""
        response = api_client.get('/api/styles/')
        
        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Test Style'
    
    def test_create_style_requires_artist(self, api_client, user):
        """일반 사용자는 스타일 생성 불가"""
        api_client.force_authenticate(user=user)
        
        data = {
            'name': 'New Style',
            'description': 'Description',
            'generation_cost_tokens': 150
        }

        response = api_client.post('/api/styles/', data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_style_success(self, api_client, artist):
        """작가는 스타일 생성 가능"""
        api_client.force_authenticate(user=artist)

        data = {
            'name': 'New Style',
            'description': 'Description',
            'generation_cost_tokens': 150
        }
        
        response = api_client.post('/api/styles/', data)
        
        assert response.status_code == status.HTTP_201_CREATED
        assert response.data['name'] == 'New Style'
        assert response.data['artist_name'] == artist.username
    
    def test_train_style(self, api_client, artist, style_model, mocker):
        """스타일 학습 요청"""
        api_client.force_authenticate(user=artist)
        
        # RabbitMQ mock
        mock_rabbitmq = mocker.patch(
            'app.services.rabbitmq_service.RabbitMQService.publish_training_task'
        )
        
        response = api_client.post(f'/api/styles/{style_model.id}/train/')

        assert response.status_code == status.HTTP_200_OK
        assert response.data['training_status'] == 'training'
        mock_rabbitmq.assert_called_once()
```

### 10.4 Mocking

```python
import pytest
from unittest.mock import Mock, patch

def test_generation_with_rabbitmq_mock(api_client, user, style_model, mocker):
    """RabbitMQ mock을 사용한 생성 테스트"""
    api_client.force_authenticate(user=user)
    
    # RabbitMQ publish mock
    mock_publish = mocker.patch(
        'app.services.rabbitmq_service.RabbitMQService.publish_generation_task'
    )
    
    data = {
        'style_id': style_model.id,
        'prompt': 'a beautiful sunset',
    }
    
    response = api_client.post('/api/generations/', data)
    
    assert response.status_code == status.HTTP_201_CREATED
    mock_publish.assert_called_once()
    
    # 호출 인자 확인
    call_args = mock_publish.call_args
    assert call_args[1]['style_id'] == style_model.id
    assert call_args[1]['prompt'] == 'a beautiful sunset'
```

---

## 참고 자료

- **[DRF 공식 문서](https://www.django-rest-framework.org/)** - API Guide
- **[docs/API.md](../../docs/API.md)** - 전체 API 명세
- **[docs/database/README.md](../../docs/database/README.md)** - DB 스키마
- **[docs/PATTERNS.md](../../docs/PATTERNS.md)** - 공통 패턴
- **[PLAN.md](PLAN.md)** - 개발 계획