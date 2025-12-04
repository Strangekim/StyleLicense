"""
Style ViewSet for Style Model API.

Endpoints:
- GET /api/styles/ - List styles with filtering and sorting
- GET /api/styles/:id/ - Retrieve style detail
- POST /api/styles/ - Create new style and start training
- DELETE /api/styles/:id/ - Delete style (owner only)
"""
import logging

from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.db.models import Q, Prefetch

from app.models import Style, Artwork, StyleTag
from app.serializers import (
    StyleListSerializer,
    StyleDetailSerializer,
    StyleCreateSerializer,
)
from app.views.base import BaseViewSet
from app.permissions import IsArtist, IsOwnerOrReadOnly
from app.services.rabbitmq_service import get_rabbitmq_service


logger = logging.getLogger(__name__)


class StyleViewSet(BaseViewSet):
    """
    ViewSet for Style model CRUD operations.

    Permissions:
    - list, retrieve: Anyone can view completed styles
    - create: Only artists
    - update, delete: Only owner

    Filtering:
    - ?tags=watercolor,portrait - Filter by tags (AND logic)
    - ?artist_id=123 - Filter by artist
    - ?training_status=completed - Filter by status

    Sorting:
    - ?sort=popular - Sort by usage_count DESC
    - ?sort=created_at - Sort by created_at DESC (default)
    - ?sort=-created_at - Sort by created_at ASC
    """

    queryset = Style.objects.all()
    serializer_class = StyleListSerializer

    def get_permissions(self):
        """Set permissions based on action."""
        if self.action in ["list", "retrieve"]:
            permission_classes = [AllowAny]
        elif self.action == "create":
            permission_classes = [IsAuthenticated, IsArtist]
        elif self.action in ["update", "partial_update", "destroy"]:
            permission_classes = [IsAuthenticated, IsOwnerOrReadOnly]
        else:
            permission_classes = [IsAuthenticated]

        return [permission() for permission in permission_classes]

    def get_serializer_class(self):
        """Use different serializers by action."""
        if self.action == "list":
            return StyleListSerializer
        elif self.action == "retrieve":
            return StyleDetailSerializer
        elif self.action == "create":
            return StyleCreateSerializer
        return StyleListSerializer

    def get_queryset(self):
        """
        Optimize queryset with select_related and prefetch_related.
        Apply filtering based on query parameters.
        """
        queryset = super().get_queryset()

        # Optimize queries
        queryset = queryset.select_related("artist").prefetch_related(
            Prefetch(
                "style_tags",
                queryset=StyleTag.objects.select_related("tag").order_by("sequence"),
            ),
            Prefetch("artworks", queryset=Artwork.objects.filter(is_valid=True)),
        )

        # Filter: Only show active styles
        queryset = queryset.filter(is_active=True)

        # Filter: Only show completed styles for non-owners
        if not self.request.user.is_authenticated or self.request.user.role != "artist":
            queryset = queryset.filter(training_status="completed")
        elif self.request.user.is_authenticated and self.request.user.role == "artist":
            # Artists see their own styles regardless of status
            queryset = queryset.filter(
                Q(training_status="completed") | Q(artist=self.request.user)
            )

        # Filter by tags (AND logic)
        tags_param = self.request.query_params.get("tags")
        if tags_param:
            tag_names = [tag.strip().lower() for tag in tags_param.split(",")]
            # Filter styles that have ALL specified tags
            for tag_name in tag_names:
                queryset = queryset.filter(style_tags__tag__name=tag_name)
            # Distinct to avoid duplicates
            queryset = queryset.distinct()

        # Filter by artist
        artist_id = self.request.query_params.get("artist_id")
        if artist_id:
            queryset = queryset.filter(artist_id=artist_id)

        # Filter by training status
        training_status = self.request.query_params.get("training_status")
        if training_status and training_status in [
            "pending",
            "training",
            "completed",
            "failed",
        ]:
            queryset = queryset.filter(training_status=training_status)

        # Sorting
        sort_param = self.request.query_params.get("sort", "-created_at")
        if sort_param == "popular":
            queryset = queryset.order_by("-usage_count", "-created_at")
        elif sort_param == "created_at":
            queryset = queryset.order_by("-created_at")
        elif sort_param == "-created_at":
            queryset = queryset.order_by("created_at")
        else:
            # Default: most recent first
            queryset = queryset.order_by("-created_at")

        return queryset

    def retrieve(self, request, *args, **kwargs):
        """Retrieve style detail."""
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "data": serializer.data})

    def perform_create(self, serializer):
        """Set artist before saving."""
        serializer.save(artist=self.request.user)

    def create(self, request, *args, **kwargs):
        """
        Create new style and start training.

        This endpoint handles:
        1. Style creation with metadata
        2. Image upload validation
        3. Artwork record creation
        4. Tag assignment
        5. Send training task to RabbitMQ

        Request format: multipart/form-data
        - name: string
        - description: string
        - generation_cost_tokens: integer
        - license_type: string
        - tags: array of strings
        - training_images: array of files (10-100 images)
        """
        try:
            logger.info(f"[Style Create] Request data keys: {list(request.data.keys())}")
            logger.info(f"[Style Create] Request FILES keys: {list(request.FILES.keys())}")

            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)

            logger.info(f"[Style Create] Validation passed, saving style...")
        except Exception as e:
            logger.error(f"[Style Create] Validation error: {str(e)}", exc_info=True)
            raise

        # Save style (serializer handles artworks and tags creation)
        try:
            logger.info(f"[Style Create] Calling perform_create with user: {request.user.id}")
            self.perform_create(serializer)
            style = serializer.instance
            logger.info(f"[Style Create] Style created: id={style.id}, name={style.name}")
        except Exception as e:
            logger.error(f"[Style Create] Error during save: {str(e)}", exc_info=True)
            raise

        # Get training images and captions from request
        training_images = request.FILES.getlist("training_images")
        captions = request.POST.getlist("captions")

        # Upload images to GCS and update Artwork records
        from app.services.gcs_service import get_gcs_service

        gcs_service = get_gcs_service()
        image_paths = []
        artworks = style.artworks.all()

        for idx, (artwork, image_file) in enumerate(zip(artworks, training_images)):
            try:
                # Get caption for this image (if available)
                caption = captions[idx] if idx < len(captions) else None

                # Upload to GCS (with caption)
                gcs_uri = gcs_service.upload_training_image(
                    style_id=style.id,
                    image_file=image_file.file,
                    image_index=idx,
                    filename=image_file.name,
                    caption=caption
                )

                # Update artwork with GCS URI and caption
                artwork.image_url = gcs_uri
                artwork.caption = caption
                artwork.is_valid = True
                artwork.save(update_fields=["image_url", "caption", "is_valid"])
                image_paths.append(gcs_uri)

            except Exception as e:
                logger.error(f"Failed to upload image {idx} for style {style.id}: {e}")
                # Mark as invalid if upload fails
                artwork.is_valid = False
                artwork.save(update_fields=["is_valid"])

        # Send training task to RabbitMQ
        task_id = None
        warning_message = None

        try:
            rabbitmq_service = get_rabbitmq_service()
            task_id = rabbitmq_service.send_training_task(
                style_id=style.id, image_paths=image_paths, num_epochs=200
            )

            # Update style status to training
            style.training_status = "training"
            style.save(update_fields=["training_status"])

        except Exception as e:
            # If RabbitMQ fails, keep style as pending
            # This allows manual training trigger later
            style.training_status = "pending"
            style.save(update_fields=["training_status"])

            warning_message = f"Style created but training task could not be submitted: {str(e)}"
            logger.warning("RabbitMQ connection failed for style %d: %s", style.id, str(e))

        # Return response with style data
        response_serializer = StyleDetailSerializer(style)
        response_data = {
            "success": True,
            "data": response_serializer.data,
            "message": "Style created successfully",
        }

        if task_id:
            response_data["task_id"] = task_id
            response_data["message"] = "Training task submitted successfully"

        if warning_message:
            response_data["warning"] = warning_message

        return Response(response_data, status=status.HTTP_201_CREATED)

    def destroy(self, request, *args, **kwargs):
        """
        Delete style (soft delete or hard delete).

        Only owner can delete their styles.
        For now, we use soft delete (set is_active=False).
        """
        instance = self.get_object()

        # Check if user is owner
        if instance.artist != request.user:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "PERMISSION_DENIED",
                        "message": "You can only delete your own styles",
                    },
                },
                status=status.HTTP_403_FORBIDDEN,
            )

        # Soft delete
        instance.is_active = False
        instance.save(update_fields=["is_active"])

        return Response(
            {"success": True, "message": "Style deleted successfully"},
            status=status.HTTP_204_NO_CONTENT,
        )
