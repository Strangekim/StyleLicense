"""
Generation Views

Handles image generation requests and status polling.
"""

from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework import permissions
from django.db import transaction

from app.models.generation import Generation
from app.models.style import Style
from app.services.token_service import TokenService
from app.services.rabbitmq_service import get_rabbitmq_service


class GenerationViewSet(viewsets.ViewSet):
    """ViewSet for image generation"""

    permission_classes = [permissions.AllowAny]

    # Cost calculation based on aspect ratio
    # TODO: Move to settings or database configuration
    COST_MAP = {
        "1:1": 50,  # 512x512
        "2:2": 75,  # 1024x1024
        "1:2": 60,  # 512x1024
    }

    def create(self, request):
        """
        Create a new generation request

        API: POST /api/generations
        Payload: {style_id, prompt_tags, description, aspect_ratio, seed}
        """
        user = request.user
        style_id = request.data.get("style_id")
        prompt_tags = request.data.get("prompt_tags", [])
        description = request.data.get("description", "")
        aspect_ratio = request.data.get("aspect_ratio", "1:1")
        seed = request.data.get("seed")

        # Validation
        if not style_id:
            return Response(
                {"error": "style_id is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if not prompt_tags or not isinstance(prompt_tags, list):
            return Response(
                {"error": "prompt_tags must be a non-empty array"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if aspect_ratio not in self.COST_MAP:
            return Response(
                {
                    "error": f"Invalid aspect_ratio. Must be one of: {list(self.COST_MAP.keys())}"
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Check if style exists and is ready
        try:
            style = Style.objects.get(id=style_id)
        except Style.DoesNotExist:
            return Response(
                {"error": "Style not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        if style.training_status != "completed":
            return Response(
                {
                    "error": "Style training is not completed",
                    "training_status": style.training_status,
                },
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        if not style.model_path:
            return Response(
                {"error": "Style model path is not available"},
                status=status.HTTP_422_UNPROCESSABLE_ENTITY,
            )

        # Calculate cost
        cost = self.COST_MAP[aspect_ratio]

        # Atomic transaction: consume tokens + create generation + send to queue
        try:
            with transaction.atomic():
                # Consume tokens
                TokenService.consume_tokens(
                    user_id=user.id,
                    amount=cost,
                    reason=f"Image generation using style '{style.name}'",
                )

                # Create generation record
                generation = Generation.objects.create(
                    user=user,
                    style=style,
                    description=description,
                    aspect_ratio=aspect_ratio,
                    seed=seed,
                    consumed_tokens=cost,
                    status="queued",
                    generation_progress={
                        "prompt_tags": prompt_tags,
                    },
                )

                # Get artist signature path
                signature_path = None
                try:
                    if hasattr(style.artist, 'artist_profile') and style.artist.artist_profile:
                        signature_path = style.artist.artist_profile.signature_image_url
                except Exception as e:
                    # Log error but don't fail generation
                    import logging
                    logger = logging.getLogger(__name__)
                    logger.warning(f"Failed to get signature for style {style.id}: {e}")

                # Send to RabbitMQ
                rabbitmq = get_rabbitmq_service()
                task_id = rabbitmq.send_generation_task(
                    generation_id=generation.id,
                    style_id=style.id,
                    lora_path=style.model_path,
                    prompt=", ".join(prompt_tags),
                    aspect_ratio=aspect_ratio,
                    seed=seed,
                    signature_path=signature_path,
                )

                # Store task_id in generation_progress
                if not generation.generation_progress:
                    generation.generation_progress = {}
                generation.generation_progress["task_id"] = task_id
                generation.save(update_fields=["generation_progress"])

        except ValueError as e:
            # Insufficient tokens or other validation error
            return Response(
                {"error": str(e)},
                status=status.HTTP_402_PAYMENT_REQUIRED,
            )

        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"[Generation] Failed to create generation: {str(e)}")
            logger.error(f"[Generation] Traceback: {traceback.format_exc()}")
            return Response(
                {"error": f"Failed to create generation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        # Return response
        return Response(
            {
                "success": True,
                "data": {
                    "id": generation.id,
                    "user_id": user.id,
                    "style_id": style.id,
                    "status": generation.status,
                    "consumed_tokens": cost,
                    "aspect_ratio": aspect_ratio,
                    "created_at": generation.created_at.isoformat(),
                    "progress": None,
                },
            },
            status=status.HTTP_201_CREATED,
        )

    def retrieve(self, request, pk=None):
        """
        Get generation status

        API: GET /api/generations/:id
        """
        try:
            user = request.user

            try:
                generation = Generation.objects.select_related(
                    "user", "style", "style__artist"
                ).get(id=pk)
            except Generation.DoesNotExist:
                return Response(
                    {"error": "Generation not found"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Check ownership (user can only see their own generations or public ones)
            if generation.user != user and not generation.is_public:
                return Response(
                    {"error": "You do not have permission to view this generation"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            # Build response based on status
            response_data = {
                "id": generation.id,
                "user_id": generation.user.id,
                "status": generation.status,
                "consumed_tokens": generation.consumed_tokens,
                "created_at": generation.created_at.isoformat(),
                "updated_at": generation.updated_at.isoformat(),
            }

            # Add progress if processing
            if generation.status == "processing" and generation.generation_progress:
                response_data["progress"] = {
                    **generation.generation_progress,
                    "last_updated": generation.updated_at.isoformat(),
                }
            else:
                response_data["progress"] = None

            # Add result if completed
            if generation.status == "completed":
                # Convert GCS URI to HTTPS URL for browser compatibility
                result_url = generation.result_url
                if result_url and result_url.startswith("gs://"):
                    result_url = result_url.replace("gs://", "https://storage.googleapis.com/", 1)

                response_data.update(
                    {
                        "style": {
                            "id": generation.style.id,
                            "name": generation.style.name,
                            "artist": {
                                "id": generation.style.artist.id,
                                "artist_name": getattr(
                                    generation.style.artist,
                                    "artist_name",
                                    generation.style.artist.username,
                                ),
                            },
                        },
                        "result_url": result_url,
                        "description": generation.description,
                        "aspect_ratio": generation.aspect_ratio,
                        "is_public": generation.is_public,
                        "like_count": generation.like_count,
                        "comment_count": generation.comment_count,
                        "tags": generation.generation_progress.get("prompt_tags", [])
                        if generation.generation_progress
                        else [],
                    }
                )

            # Add error info if failed
            if generation.status == "failed":
                error_message = None
                if generation.generation_progress:
                    error_message = generation.generation_progress.get("error_message")
                response_data["error_message"] = error_message
                response_data["refunded"] = True  # Tokens are refunded in webhook

            return Response({"success": True, "data": response_data})

        except Exception as e:
            import logging
            import traceback
            logger = logging.getLogger(__name__)
            logger.error(f"[Generation] Failed to retrieve generation {pk}: {str(e)}")
            logger.error(f"[Generation] Traceback: {traceback.format_exc()}")
            return Response(
                {"error": f"Failed to retrieve generation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    @action(detail=True, methods=["patch"], permission_classes=[permissions.IsAuthenticated])
    def update_details(self, request, pk=None):
        """
        Update generation details (description and/or visibility)

        API: PATCH /api/generations/:id/update_details
        Payload: { description: str, is_public: bool }
        """
        try:
            generation = Generation.objects.get(id=pk)
        except Generation.DoesNotExist:
            return Response(
                {"error": "Generation not found"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Check ownership
        if generation.user != request.user:
            return Response(
                {"error": "You do not have permission to update this generation"},
                status=status.HTTP_403_FORBIDDEN,
            )

        # Update fields
        description = request.data.get("description")
        is_public = request.data.get("is_public")

        if description is not None:
            generation.description = description

        if is_public is not None:
            generation.is_public = is_public

        generation.save(update_fields=["description", "is_public"])

        return Response(
            {
                "success": True,
                "data": {
                    "id": generation.id,
                    "description": generation.description,
                    "is_public": generation.is_public,
                },
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        """
        Get current user's generations.

        GET /api/generations/me?limit=50&status=completed&visibility=public
        """
        user = request.user
        limit = int(request.query_params.get("limit", 50))
        status_filter = request.query_params.get("status")
        visibility_filter = request.query_params.get("visibility")

        # Build queryset
        queryset = Generation.objects.filter(user=user).order_by("-created_at")

        # Apply filters
        if status_filter:
            queryset = queryset.filter(status=status_filter)

        if visibility_filter:
            if visibility_filter == "public":
                queryset = queryset.filter(is_public=True)
            elif visibility_filter == "private":
                queryset = queryset.filter(is_public=False)

        # Limit results
        generations = queryset[:limit]

        # Serialize
        results = []
        for gen in generations:
            gen_data = {
                "id": gen.id,
                "status": gen.status,
                "created_at": gen.created_at.isoformat(),
                "visibility": "public" if gen.is_public else "private",
            }

            # Add result data if completed
            if gen.status == "completed":
                # Convert GCS URI to HTTPS URL for browser compatibility
                result_url = gen.result_url
                if result_url and result_url.startswith("gs://"):
                    result_url = result_url.replace("gs://", "https://storage.googleapis.com/", 1)

                gen_data.update(
                    {
                        "result_url": result_url,
                        "description": gen.description,
                        "like_count": gen.like_count,
                        "comment_count": gen.comment_count,
                        "is_liked_by_current_user": False,  # TODO: Implement
                    }
                )

            results.append(gen_data)

        return Response(
            {
                "success": True,
                "data": {
                    "generations": results,
                    "count": len(results),
                },
            }
        )
