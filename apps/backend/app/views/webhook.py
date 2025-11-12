"""
Webhook Views

Receives callbacks from AI servers (training-server, inference-server)
for training and generation progress/completion updates.
"""

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.views.decorators.csrf import csrf_exempt
from django.db import transaction

from app.models.style import Style
from app.models.generation import Generation
from app.models.notification import Notification
from app.services.token_service import TokenService


# ============================================================================
# Training Webhooks
# ============================================================================


@csrf_exempt
@api_view(["PATCH"])
@permission_classes([AllowAny])  # Authenticated by WebhookAuthMiddleware
def training_progress(request):
    """
    Update training progress

    API Spec: PATCH /api/webhooks/training/progress
    Payload: {style_id, progress: {current_epoch, total_epochs, progress_percent, estimated_seconds}}
    """
    style_id = request.data.get("style_id")
    progress_data = request.data.get("progress", {})

    if not style_id:
        return Response(
            {"error": "style_id is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        style_model = Style.objects.get(id=style_id)

        # Update progress JSONB field
        style_model.training_progress = progress_data
        style_model.save(update_fields=["training_progress"])

        return Response({"success": True})

    except Style.DoesNotExist:
        return Response({"error": "Style not found"}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def training_complete(request):
    """
    Training completion notification

    API Spec: POST /api/webhooks/training/complete
    Payload: {style_id, model_path, training_metric: {loss, epochs}}
    """
    style_id = request.data.get("style_id")
    model_path = request.data.get("model_path")
    training_metric = request.data.get("training_metric", {})

    if not style_id:
        return Response(
            {"error": "style_id is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    if not model_path:
        return Response(
            {"error": "model_path is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            style_model = Style.objects.select_for_update().get(id=style_id)

            # Update style model
            style_model.training_status = "completed"
            style_model.model_path = model_path
            style_model.training_metric = training_metric
            style_model.training_progress = None  # Clear progress
            style_model.save(
                update_fields=[
                    "training_status",
                    "model_path",
                    "training_metric",
                    "training_progress",
                ]
            )

            # Create notification for artist
            Notification.objects.create(
                recipient=style_model.user,
                actor=None,  # System notification
                type="style_training_complete",
                target_type="style",
                target_id=style_model.id,
                metadata={
                    "style_name": style_model.name,
                    "model_path": model_path,
                    "training_metric": training_metric,
                },
            )

        return Response({"success": True})

    except Style.DoesNotExist:
        return Response({"error": "Style not found"}, status=status.HTTP_404_NOT_FOUND)


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def training_failed(request):
    """
    Training failure notification

    API Spec: POST /api/webhooks/training/failed
    Payload: {style_id, error_message, error_code}
    """
    style_id = request.data.get("style_id")
    error_message = request.data.get("error_message", "Unknown error")
    error_code = request.data.get("error_code", "TRAINING_FAILED")

    if not style_id:
        return Response(
            {"error": "style_id is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            style_model = Style.objects.select_for_update().get(id=style_id)

            # Update style model
            style_model.training_status = "failed"
            style_model.training_progress = None  # Clear progress
            style_model.save(update_fields=["training_status", "training_progress"])

            # Create notification for artist
            Notification.objects.create(
                recipient=style_model.user,
                actor=None,  # System notification
                type="style_training_failed",
                target_type="style",
                target_id=style_model.id,
                metadata={
                    "style_name": style_model.name,
                    "error_message": error_message,
                    "error_code": error_code,
                },
            )

        return Response({"success": True})

    except Style.DoesNotExist:
        return Response({"error": "Style not found"}, status=status.HTTP_404_NOT_FOUND)


# ============================================================================
# Inference Webhooks
# ============================================================================


@csrf_exempt
@api_view(["PATCH"])
@permission_classes([AllowAny])
def inference_progress(request):
    """
    Update generation progress

    API Spec: PATCH /api/webhooks/inference/progress
    Payload: {generation_id, progress: {current_step, total_steps, progress_percent, estimated_seconds}}
    """
    generation_id = request.data.get("generation_id")
    progress_data = request.data.get("progress", {})

    if not generation_id:
        return Response(
            {"error": "generation_id is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        generation = Generation.objects.get(id=generation_id)

        # Update progress JSONB field
        generation.generation_progress = progress_data
        generation.save(update_fields=["generation_progress"])

        return Response({"success": True})

    except Generation.DoesNotExist:
        return Response(
            {"error": "Generation not found"}, status=status.HTTP_404_NOT_FOUND
        )


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def inference_complete(request):
    """
    Generation completion notification

    API Spec: POST /api/webhooks/inference/complete
    Payload: {generation_id, result_url, metadata: {seed, steps, guidance_scale}}
    """
    generation_id = request.data.get("generation_id")
    result_url = request.data.get("result_url")
    metadata = request.data.get("metadata", {})

    if not generation_id:
        return Response(
            {"error": "generation_id is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    if not result_url:
        return Response(
            {"error": "result_url is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            generation = Generation.objects.select_for_update().get(id=generation_id)

            # Update generation
            generation.status = "completed"
            generation.result_url = result_url
            generation.generation_progress = None  # Clear progress

            # Merge metadata
            if generation.metadata:
                generation.metadata.update(metadata)
            else:
                generation.metadata = metadata

            generation.save(
                update_fields=[
                    "status",
                    "result_url",
                    "generation_progress",
                    "metadata",
                ]
            )

            # Create notification for user (optional - user might be polling)
            # Notification.objects.create(...)

        return Response({"success": True})

    except Generation.DoesNotExist:
        return Response(
            {"error": "Generation not found"}, status=status.HTTP_404_NOT_FOUND
        )


@csrf_exempt
@api_view(["POST"])
@permission_classes([AllowAny])
def inference_failed(request):
    """
    Generation failure notification

    API Spec: POST /api/webhooks/inference/failed
    Payload: {generation_id, error_message, error_code}
    """
    generation_id = request.data.get("generation_id")
    error_message = request.data.get("error_message", "Unknown error")
    error_code = request.data.get("error_code", "GENERATION_FAILED")

    if not generation_id:
        return Response(
            {"error": "generation_id is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        with transaction.atomic():
            generation = Generation.objects.select_for_update().get(id=generation_id)

            # Refund tokens
            TokenService.refund_tokens(
                user_id=generation.user.id,
                amount=generation.cost,
                reason=f"Generation failed: {error_message}",
                related_generation_id=generation.id,
            )

            # Update generation
            generation.status = "failed"
            generation.generation_progress = None  # Clear progress

            # Store error details in metadata
            if not generation.metadata:
                generation.metadata = {}
            generation.metadata["error_message"] = error_message
            generation.metadata["error_code"] = error_code

            generation.save(update_fields=["status", "generation_progress", "metadata"])

        return Response({"success": True})

    except Generation.DoesNotExist:
        return Response(
            {"error": "Generation not found"}, status=status.HTTP_404_NOT_FOUND
        )
