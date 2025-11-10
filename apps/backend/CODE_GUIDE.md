# Backend Code Guide

**Purpose**: Provides code patterns, rules, and examples to follow when developing Backend based on Django REST Framework.

**Audience**: Backend developers, Code reviewers

---

## Table of Contents
1. [Code Writing Principles](#1-code-writing-principles)
2. [Model Patterns](#2-model-patterns)
3. [Serializer Patterns](#3-serializer-patterns)
4. [ViewSet Patterns](#4-viewset-patterns)
5. [Service Layer Patterns](#5-service-layer-patterns)
6. [RabbitMQ Patterns](#6-rabbitmq-patterns)
7. [Permission Patterns](#7-permission-patterns)
8. [Error Handling](#8-error-handling)
9. [Performance Optimization](#9-performance-optimization)
10. [Writing Tests](#10-writing-tests)

---

## 1. Code Writing Principles

### 1.1 Django REST Framework Philosophy

- **Serializers for data transformation only** - No business logic
- **Views for HTTP request/response only** - No business logic
- **Business logic in Services** - Reusable units
- **Models for data structure** - No complex logic

### 1.2 Naming Conventions

```python
# Models: Singular PascalCase
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

# Functions: snake_case, start with verb
def consume_tokens(user_id, amount):
    pass
```

### 1.3 Import Order

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

## 2. Model Patterns

### 2.1 Basic Model Structure

```python
# app/models/style.py
from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class StyleModel(models.Model):
    """AI model representing artist's style"""

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
        on_delete=models.CASCADE,  # Cascade artist deletion
        related_name='styles'
    )
    name = models.CharField(max_length=200)
    description = models.TextField()
    training_status = models.CharField(
        max_length=20,
        choices=TRAINING_STATUS_CHOICES,
        default='pending',
        db_index=True  # Frequently filtered
    )
    generation_cost_tokens = models.IntegerField(default=100)  # Token units
    model_path = models.TextField(blank=True, null=True)  # S3 path

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'styles'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['training_status', 'artist']),  # Composite index
            models.Index(fields=['-created_at']),
        ]

    def __str__(self):
        return f"{self.name} by {self.artist.username}"

    def is_ready(self):
        """Check if ready for generation"""
        return self.training_status == 'completed' and self.model_path
```

### 2.2 Related Names Convention

```python
# Foreign Key: plural
class GeneratedImage(models.Model):
    style = models.ForeignKey(
        StyleModel,
        on_delete=models.RESTRICT,
        related_name='generated_images'  # style.generated_images.all()
    )

# Many-to-Many: plural
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
        """Calculate user's current token balance"""
        transactions = cls.objects.filter(user=user)
        balance = sum(t.amount for t in transactions)
        return balance

    def is_refundable(self):
        """
        Check if refundable.

        Only generation transactions (where sender, receiver, and related_generation are all present)
        are eligible for refunds.
        """
        # Only image generation payments are refundable
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

## 3. Serializer Patterns

### 3.1 Basic ModelSerializer

```python
# app/serializers/style.py
from rest_framework import serializers
from app.models import StyleModel

class StyleModelSerializer(serializers.ModelSerializer):
    # Read-only fields
    artist_name = serializers.CharField(
        source='artist.username',
        read_only=True
    )

    # Write-only fields
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
        """Validate price"""
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
        """Validate entire data"""
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
# Read-only nested (don't use depth, use explicit serializer)
class TrainingImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = TrainingImage
        fields = ['id', 'image_url', 'tags']

class StyleModelDetailSerializer(serializers.ModelSerializer):
    training_images = TrainingImageSerializer(many=True, read_only=True)
    progress = serializers.SerializerMethodField()

    class Meta:
        model = StyleModel
        fields = [
            'id', 
            'name', 
            'training_status', 
            'progress',  # Add progress field
            'training_images', 
            'created_at'
        ]

    def get_progress(self, obj):
        """Return progress only when training."""
        if obj.training_status == 'training':
            # Assuming 'training_progress' is a JSONB field in the model
            return obj.training_progress
        return None
```

### 3.3 Writable Nested Serializers

```python
class CommentCreateSerializer(serializers.ModelSerializer):
    # Receive only parent_id when writing reply
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
    """Allow client to request only needed fields"""

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

## 4. ViewSet Patterns

### 4.1 Basic ModelViewSet

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
    """Style CRUD and training request"""

    queryset = StyleModel.objects.all()
    serializer_class = StyleModelSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        """Filter by user"""
        queryset = super().get_queryset()

        # Artist can view all their styles
        if self.request.user.role == 'artist':
            return queryset.filter(artist=self.request.user)

        # Regular users can only view completed styles
        return queryset.filter(training_status='completed')

    def get_permissions(self):
        """Set permissions by action"""
        if self.action in ['create', 'update', 'partial_update', 'destroy']:
            return [IsArtist()]
        return super().get_permissions()

    def perform_create(self, serializer):
        """Auto-assign artist on creation"""
        serializer.save(artist=self.request.user)

    @action(detail=True, methods=['post'], permission_classes=[IsArtist])
    def train(self, request, pk=None):
        """Start training custom action"""
        style = self.get_object()

        # Reject if already training
        if style.training_status == 'training':
            return Response(
                {'error': 'Training already in progress'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Deduct training cost (100 tokens)
        if not token_service.consume_tokens(
            user_id=request.user.id,
            amount=100,
            reason=f'Training style {pk}'
        ):
            return Response(
                {'error': 'Insufficient tokens'},
                status=status.HTTP_402_PAYMENT_REQUIRED
            )

        # Send training task to RabbitMQ
        rabbitmq_service.publish_training_task(
            style_id=pk,
            image_urls=style.get_training_image_urls(),
            params={'epochs': 200, 'learning_rate': 1e-4}
        )

        # Update status
        style.training_status = 'training'
        style.save()

        return Response({
            'message': 'Training started',
            'style_id': pk,
            'training_status': 'training'
        })
```

### 4.2 Custom Action Patterns

```python
class GenerationViewSet(viewsets.ModelViewSet):

    @action(detail=False, methods=['get'])
    def my_generations(self, request):
        """Query my generation history"""
        generations = GeneratedImage.objects.filter(
            user=request.user
        ).select_related('style')

        page = self.paginate_queryset(generations)
        serializer = self.get_serializer(page, many=True)
        return self.get_paginated_response(serializer.data)

    @action(detail=True, methods=['post'])
    def retry(self, request, pk=None):
        """Retry failed generation"""
        generation = self.get_object()

        if generation.status != 'FAILED':
            return Response(
                {'error': 'Only failed generations can be retried'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Retry logic...
        return Response({'message': 'Retry queued'})
```

### 4.3 ViewSet Introspection

```python
class StyleViewSet(viewsets.ModelViewSet):

    def get_permissions(self):
        """Set permissions dynamically by action"""
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
        """Use different serializer by action"""
        if self.action == 'list':
            return StyleModelListSerializer  # Simple fields only
        elif self.action == 'retrieve':
            return StyleModelDetailSerializer  # All fields
        return StyleModelSerializer  # Default
```

---

## 5. Service Layer Patterns

### 5.1 Basic Service Structure

```python
# app/services/token_service.py
from django.db import transaction
from app.models import User, TokenTransaction

class TokenService:
    """Token-related business logic"""

    @staticmethod
    @transaction.atomic
    def consume_tokens(user_id: int, amount: int, reason: str) -> bool:
        """
        Atomically deduct tokens.

        Args:
            user_id: User ID
            amount: Amount of tokens to deduct
            reason: Reason for deduction

        Returns:
            Success status

        Raises:
            User.DoesNotExist: User doesn't exist
        """
        # Prevent concurrency issues with SELECT FOR UPDATE
        user = User.objects.select_for_update().get(id=user_id)

        # Check balance
        if user.token_balance < amount:
            return False

        # Deduct
        user.token_balance -= amount
        user.save()

        # Record transaction
        # Note: transaction_type column doesn't exist in DB,
        # type is determined by combination of sender_id/receiver_id/related_generation_id.
        TokenTransaction.objects.create(
            sender_id=user_id,
            receiver_id=None,  # Paid to platform
            amount=amount,
            memo=reason
        )

        return True

    @staticmethod
    @transaction.atomic
    def refund_tokens(user_id: int, amount: int, reason: str):
        """Refund tokens"""
        user = User.objects.select_for_update().get(id=user_id)

        user.token_balance += amount
        user.save()

        # Record refund transaction
        TokenTransaction.objects.create(
            sender_id=None,  # Issued by platform
            receiver_id=user_id,
            amount=amount,
            memo=reason,
            refunded=True
        )
```

### 5.2 Service Invocation Pattern

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

        # 1. Deduct tokens (Service)
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

        # 2. Save generation request
        generation = serializer.save(user=request.user, style=style)

        # 3. Send task to RabbitMQ (Service)
        rabbitmq_service = RabbitMQService()
        try:
            rabbitmq_service.publish_generation_task(
                generation_id=generation.id,
                style_id=style_id,
                prompt=serializer.validated_data['prompt'],
                params={'size': '512x512', 'steps': 50}
            )
        except Exception as e:
            # Refund tokens on failure
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

## 6. RabbitMQ Patterns

### 6.1 Publisher (Backend → AI Server)

```python
# app/services/rabbitmq_service.py
import pika
import json
import uuid
from django.conf import settings

class RabbitMQService:
    """RabbitMQ message publishing"""

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
        """Publish training task"""
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
        """Publish image generation task"""
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

@csrf_exempt  # Exclude CSRF (authenticate with INTERNAL_API_TOKEN)
@api_view(['PATCH'])
@permission_classes([AllowAny])  # Authenticated in Middleware
def training_progress(request, style_id):
    """Update training progress"""
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
    """Training completion notification"""
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

    # Notify artist
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
    """AI server Webhook authentication middleware"""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Validate only webhook paths
        if request.path.startswith('/api/webhooks/'):
            # Parse Authorization: Bearer <TOKEN>
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

## 7. Permission Patterns

### 7.1 Custom Permissions

```python
# app/permissions/custom.py
from rest_framework import permissions

class IsArtist(permissions.BasePermission):
    """Check artist permission"""

    message = "Only artists can perform this action."

    def has_permission(self, request, view):
        return (
            request.user and
            request.user.is_authenticated and
            request.user.role == 'artist'
        )

class IsOwnerOrReadOnly(permissions.BasePermission):
    """Only owner can modify, everyone can read"""

    def has_object_permission(self, request, view, obj):
        # Allow read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for owner
        return obj.artist == request.user

class IsOwner(permissions.BasePermission):
    """Only owner can access"""

    def has_object_permission(self, request, view, obj):
        # Use obj.user or obj.artist attribute
        owner = getattr(obj, 'user', getattr(obj, 'artist', None))
        return owner == request.user
```

### 7.2 Permission Composition

```python
class StyleViewSet(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated, IsArtist]  # AND condition

    def get_permissions(self):
        """Different permissions by action"""
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        elif self.action in ['update', 'partial_update', 'destroy']:
            return [IsAuthenticated(), IsOwnerOrReadOnly()]
        return super().get_permissions()
```

---

## 8. Error Handling

### 8.1 Standard Error Response Format

```python
# app/exceptions.py
from rest_framework.exceptions import APIException
from rest_framework import status

class InsufficientTokensError(APIException):
    status_code = status.HTTP_402_PAYMENT_REQUIRED
    default_detail = 'Insufficient tokens.'
    default_code = 'insufficient_tokens'

class TrainingInProgressError(APIException):
    status_code = status.HTTP_400_BAD_REQUEST
    default_detail = 'Training already in progress.'
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
    """Custom error response format"""
    response = exception_handler(exc, context)

    if response is not None:
        # Convert to standard format
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

## 9. Performance Optimization

### 9.1 Prevent N+1 Queries

```python
# Bad: N+1 queries
class StyleViewSet(viewsets.ModelViewSet):
    def list(self, request):
        styles = StyleModel.objects.all()
        for style in styles:
            print(style.artist.username)  # Query on each iteration

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
        db_index=True  # Single column index
    )

    class Meta:
        indexes = [
            # Composite index (training_status + artist)
            models.Index(fields=['training_status', 'artist']),

            # Sorting index
            models.Index(fields=['-created_at']),

            # Search index (PostgreSQL)
            models.Index(
                fields=['name'],
                name='style_name_idx',
                opclasses=['varchar_pattern_ops']  # LIKE search
            ),
        ]
```

### 9.3 Caching

```python
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page

class StyleViewSet(viewsets.ModelViewSet):

    @method_decorator(cache_page(60 * 5))  # 5 minute cache
    def list(self, request):
        return super().list(request)

    def get_queryset(self):
        # Cache key
        cache_key = f'popular_styles_{self.request.user.id}'

        # Check cache
        cached = cache.get(cache_key)
        if cached:
            return cached

        # DB query
        queryset = StyleModel.objects.filter(
            training_status='completed'
        ).order_by('-view_count')[:10]

        # Save to cache (5 minutes)
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
            'style__artist'  # Nested relation
        ).prefetch_related(
            'likes',
            'comments__author'  # Nested relation
        ).only(  # Only needed fields
            'id',
            'image_url',
            'prompt',
            'created_at',
            'user__username',
            'style__name'
        )
```

---

## 10. Writing Tests

### 10.1 Pytest Fixtures

```python
# app/tests/conftest.py
import pytest
from app.models import User, StyleModel, TokenTransaction

@pytest.fixture
def user(db):
    """Regular user"""
    return User.objects.create_user(
        username='testuser',
        email='test@example.com',
        password='password123',
        token_balance=1000
    )

@pytest.fixture
def artist(db):
    """Artist user"""
    return User.objects.create_user(
        username='artist',
        email='artist@example.com',
        password='password123',
        role='artist',
        token_balance=5000
    )

@pytest.fixture
def style_model(db, artist):
    """Completed style model"""
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
    """DRF API client"""
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
        """Token consumption success"""
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
        """Fail on insufficient tokens"""
        result = TokenService.consume_tokens(
            user_id=user.id,
            amount=2000,  # More than balance
            reason='Test'
        )

        assert result is False

        user.refresh_from_db()
        assert user.token_balance == 1000  # No change

    @pytest.mark.django_db(transaction=True)
    def test_consume_tokens_concurrency(self, user):
        """Concurrency test"""
        from concurrent.futures import ThreadPoolExecutor

        def consume():
            return TokenService.consume_tokens(
                user_id=user.id,
                amount=100,
                reason='Concurrent test'
            )

        # 10 concurrent requests
        with ThreadPoolExecutor(max_workers=10) as executor:
            results = list(executor.map(lambda _: consume(), range(10)))

        # Should succeed 10 times
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
        """List styles"""
        response = api_client.get('/api/styles/')

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data['results']) == 1
        assert response.data['results'][0]['name'] == 'Test Style'

    def test_create_style_requires_artist(self, api_client, user):
        """Regular user cannot create style"""
        api_client.force_authenticate(user=user)

        data = {
            'name': 'New Style',
            'description': 'Description',
            'generation_cost_tokens': 150
        }

        response = api_client.post('/api/styles/', data)

        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_create_style_success(self, api_client, artist):
        """Artist can create style"""
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
        """Style training request"""
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
    """Generation test using RabbitMQ mock"""
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

    # Verify call arguments
    call_args = mock_publish.call_args
    assert call_args[1]['style_id'] == style_model.id
    assert call_args[1]['prompt'] == 'a beautiful sunset'
```

---

## References

- **[DRF Official Docs](https://www.django-rest-framework.org/)** - API Guide
- **[docs/API.md](../../docs/API.md)** - Complete API specification
- **[docs/database/README.md](../../docs/database/README.md)** - DB schema
- **[docs/PATTERNS.md](../../docs/PATTERNS.md)** - Common patterns
- **[PLAN.md](PLAN.md)** - Development plan
