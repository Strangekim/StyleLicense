"""
Base ViewSet with common pagination and query optimization.
"""
from rest_framework import viewsets
from rest_framework.pagination import CursorPagination
from rest_framework.response import Response


class CustomCursorPagination(CursorPagination):
    """
    Cursor-based pagination ordered by created_at descending.
    Supports ?cursor=<encoded_value>&limit=N query params.
    """
    page_size = 20
    page_size_query_param = 'limit'
    max_page_size = 100
    ordering = '-created_at'  # Most recent first


class BaseViewSet(viewsets.ModelViewSet):
    """
    Base ViewSet with pagination and response formatting.
    Extends Django REST Framework's ModelViewSet.
    """
    pagination_class = CustomCursorPagination

    def get_queryset(self):
        """
        Override in subclasses to add select_related/prefetch_related.
        Example:
            return super().get_queryset().select_related('user', 'artist')
        """
        return super().get_queryset()

    def list(self, request, *args, **kwargs):
        """
        Override list to provide consistent response format.
        Returns paginated results with standard structure.
        """
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def retrieve(self, request, *args, **kwargs):
        """
        Override retrieve to provide consistent response format.
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            'success': True,
            'data': serializer.data
        })

    def create(self, request, *args, **kwargs):
        """
        Override create to provide consistent response format.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Created successfully'
        }, status=201, headers=headers)

    def update(self, request, *args, **kwargs):
        """
        Override update to provide consistent response format.
        """
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        if getattr(instance, '_prefetched_objects_cache', None):
            instance._prefetched_objects_cache = {}

        return Response({
            'success': True,
            'data': serializer.data,
            'message': 'Updated successfully'
        })

    def destroy(self, request, *args, **kwargs):
        """
        Override destroy to provide consistent response format.
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({
            'success': True,
            'message': 'Deleted successfully'
        }, status=204)
