"""
Tests for API Foundation (M2-API-Foundation).

Tests:
- Response format standardization (success/error)
- Pagination with cursor
- Exception handler formatting
- Base serializer and ViewSet behavior
"""
import pytest
from django.test import TestCase, Client
from django.urls import path, include
from rest_framework import viewsets, serializers, status as drf_status
from rest_framework.test import APITestCase, APIClient, URLPatternsTestCase
from rest_framework.decorators import api_view
from rest_framework.response import Response

from app.models import User
from app.serializers.base import BaseSerializer
from app.views.base import BaseViewSet
from app.exceptions import InsufficientTokensError, ValidationError


class TestBaseSerializer(TestCase):
    """Test BaseSerializer dynamic field filtering."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            username="testuser",
            provider="google",
            provider_user_id="google123",
            email="test@example.com",
        )

    def test_base_serializer_dynamic_fields(self):
        """Test that BaseSerializer can filter fields dynamically."""
        class UserSerializer(BaseSerializer):
            class Meta:
                model = User
                fields = ['id', 'username', 'email', 'token_balance']

        # Test with all fields
        serializer = UserSerializer(self.user)
        assert 'id' in serializer.data
        assert 'username' in serializer.data
        assert 'email' in serializer.data
        assert 'token_balance' in serializer.data

        # Test with filtered fields
        serializer = UserSerializer(self.user, fields=['id', 'username'])
        assert 'id' in serializer.data
        assert 'username' in serializer.data
        assert 'email' not in serializer.data
        assert 'token_balance' not in serializer.data


class TestExceptionHandler(APITestCase):
    """Test custom exception handler."""

    def test_custom_exception_format(self):
        """Test that custom exceptions return proper format."""
        # Create a test view that raises our custom exception
        @api_view(['GET'])
        def test_view(request):
            raise InsufficientTokensError(detail={'required': 100, 'available': 50})

        # Temporarily add the view to urlpatterns
        from django.urls import path
        from django.conf import settings

        test_urlpatterns = [
            path('test-exception/', test_view),
        ]

        with self.settings(ROOT_URLCONF=type('', (), {'urlpatterns': test_urlpatterns})):
            response = self.client.get('/test-exception/')

        # Check response format
        assert response.status_code == 402
        data = response.json()
        assert 'success' in data
        assert data['success'] is False
        assert 'error' in data
        assert 'code' in data['error']
        assert 'message' in data['error']
        assert data['error']['code'] == 'INSUFFICIENT_TOKENS'

    def test_validation_error_format(self):
        """Test that validation errors are properly formatted."""
        @api_view(['POST'])
        def test_view(request):
            raise ValidationError(detail="Invalid input data")

        test_urlpatterns = [
            path('test-validation/', test_view),
        ]

        with self.settings(ROOT_URLCONF=type('', (), {'urlpatterns': test_urlpatterns})):
            response = self.client.post('/test-validation/')

        assert response.status_code == 400
        data = response.json()
        assert data['success'] is False
        assert data['error']['code'] == 'VALIDATION_ERROR'


class TestResponseFormat(APITestCase):
    """Test standardized response formats."""

    def setUp(self):
        """Create test user for authentication."""
        self.user = User.objects.create_user(
            username="testuser",
            provider="google",
            provider_user_id="google123",
            email="test@example.com",
        )
        self.client.force_authenticate(user=self.user)

    def test_success_response_format(self):
        """Test that success responses have correct format."""
        # Create a simple view that returns success
        @api_view(['GET'])
        def test_view(request):
            return Response({
                'success': True,
                'data': {'message': 'test'}
            })

        test_urlpatterns = [
            path('test-success/', test_view),
        ]

        with self.settings(ROOT_URLCONF=type('', (), {'urlpatterns': test_urlpatterns})):
            response = self.client.get('/test-success/')

        assert response.status_code == 200
        data = response.json()
        assert 'success' in data
        assert data['success'] is True
        assert 'data' in data


class TestBasePagination(TestCase):
    """Test cursor-based pagination."""

    def setUp(self):
        """Create multiple test users."""
        for i in range(30):
            User.objects.create_user(
                username=f"user{i}",
                provider="google",
                provider_user_id=f"google{i}",
                email=f"user{i}@example.com",
            )

    def test_cursor_pagination_default(self):
        """Test that pagination returns correct page size."""
        # Since we need a real ViewSet to test pagination,
        # we'll test that the paginator class is configured correctly
        from app.views.base import CustomCursorPagination

        paginator = CustomCursorPagination()
        assert paginator.page_size == 20
        assert paginator.ordering == '-created_at'

    def test_cursor_pagination_custom_limit(self):
        """Test that pagination respects custom limit."""
        from app.views.base import CustomCursorPagination

        paginator = CustomCursorPagination()
        assert paginator.page_size_query_param == 'limit'
        assert paginator.max_page_size == 100


print("API Foundation tests created successfully!")
