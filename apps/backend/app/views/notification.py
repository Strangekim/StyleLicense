"""
Notification views for listing and managing user notifications.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination

from app.models import Notification
from app.serializers.notification import NotificationSerializer, MarkAsReadSerializer


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for user notifications.

    list: Get all notifications for current user (paginated, sorted by created_at DESC)
    retrieve: Get specific notification
    mark_as_read: Mark notification as read (PATCH /api/notifications/:id/read)
    mark_all_as_read: Mark all notifications as read (POST /api/notifications/mark-all-read)
    """

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = PageNumberPagination
    ordering = ["-created_at"]

    def get_queryset(self):
        """Return notifications for current user only."""
        return (
            Notification.objects.filter(recipient=self.request.user)
            .select_related("actor")
            .order_by("-created_at")
        )

    def list(self, request, *args, **kwargs):
        """
        List all notifications for current user.

        Query params:
        - unread_only: true/false (filter only unread notifications)

        Response includes:
        - count: total count
        - unread_count: number of unread notifications
        - results: paginated notifications
        """
        queryset = self.get_queryset()

        # Filter unread only if requested
        unread_only = request.query_params.get("unread_only", "false").lower() == "true"
        if unread_only:
            queryset = queryset.filter(is_read=False)

        # Get unread count
        unread_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).count()

        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            response = self.get_paginated_response(serializer.data)
            response.data["unread_count"] = unread_count
            return response

        serializer = self.get_serializer(queryset, many=True)
        return Response({"unread_count": unread_count, "results": serializer.data})

    @action(detail=True, methods=["patch"], url_path="read")
    def mark_as_read(self, request, pk=None):
        """
        Mark specific notification as read.

        PATCH /api/notifications/:id/read
        Body: {"is_read": true}
        """
        notification = self.get_object()

        # Verify ownership
        if notification.recipient != request.user:
            return Response(
                {"error": "Permission denied"}, status=status.HTTP_403_FORBIDDEN
            )

        serializer = MarkAsReadSerializer(data=request.data)
        if serializer.is_valid():
            notification.is_read = serializer.validated_data.get("is_read", True)
            notification.save()

            return Response(
                NotificationSerializer(notification).data, status=status.HTTP_200_OK
            )

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], url_path="mark-all-read")
    def mark_all_as_read(self, request):
        """
        Mark all unread notifications as read for current user.

        POST /api/notifications/mark-all-read
        """
        updated_count = Notification.objects.filter(
            recipient=request.user, is_read=False
        ).update(is_read=True)

        return Response(
            {
                "message": "All notifications marked as read",
                "updated_count": updated_count,
            },
            status=status.HTTP_200_OK,
        )
