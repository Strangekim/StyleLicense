"""
Tag ViewSet for Tag System API.

Endpoints:
- GET /api/tags/ - List popular tags
- GET /api/tags/?search=water - Autocomplete search
"""
from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import AllowAny

from app.models import Tag
from app.serializers import TagSerializer


class TagViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for Tag model (read-only).

    Provides:
    - List of popular tags (usage_count > 0)
    - Autocomplete search by tag name

    Permissions:
    - AllowAny (public endpoint)

    Endpoints:
    - GET /api/tags/ - List popular tags
    - GET /api/tags/?search=water - Search tags by name (autocomplete)
    - GET /api/tags/:id/ - Get tag detail
    """

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]

    def get_queryset(self):
        """
        Optimize queryset and apply filters.

        Filters:
        - Only active tags (is_active=True)
        - Only tags with usage_count > 0
        - Search by name (for autocomplete)
        """
        queryset = super().get_queryset()

        # Only active tags
        queryset = queryset.filter(is_active=True)

        # Only tags with usage_count > 0
        queryset = queryset.filter(usage_count__gt=0)

        # Search by name (autocomplete)
        search = self.request.query_params.get("search")
        if search:
            # Case-insensitive search
            queryset = queryset.filter(name__icontains=search)

        # Order by usage_count DESC (most popular first)
        queryset = queryset.order_by("-usage_count", "name")

        # Limit to top 20 tags only for list action (not for retrieve)
        if not search and self.action == "list":
            queryset = queryset[:20]

        return queryset

    def list(self, request, *args, **kwargs):
        """
        List popular tags.

        Returns top 20 tags by usage_count (or filtered by search).

        Response:
        {
            "success": true,
            "data": [
                {"id": 1, "name": "watercolor", "usage_count": 50},
                {"id": 2, "name": "portrait", "usage_count": 30},
                ...
            ]
        }
        """
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "data": serializer.data})

    def retrieve(self, request, *args, **kwargs):
        """
        Retrieve tag detail.

        Response:
        {
            "success": true,
            "data": {
                "id": 1,
                "name": "watercolor",
                "usage_count": 50
            }
        }
        """
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "data": serializer.data})
