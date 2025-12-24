"""
URL configuration for app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from app.views.auth import GoogleLoginView, GoogleCallbackView, LogoutView, MeView
from app.views.health import HealthCheckView
from app.views.style import StyleViewSet
from app.views.token import TokenViewSet
from app.views.tag import TagViewSet
from app.views.notification import NotificationViewSet
from app.views.generation import GenerationViewSet as ImageGenerationViewSet
from app.views.community import (
    CommunityViewSet,
    GenerationViewSet as CommunityImageViewSet,
    CommentViewSet,
    UserViewSet,
)
from app.views import webhook

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r"styles", StyleViewSet, basename="style")
router.register(r"tokens", TokenViewSet, basename="token")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"community", CommunityViewSet, basename="community")
router.register(r"generations", ImageGenerationViewSet, basename="generation")  # For creating/polling generations
router.register(r"images", CommunityImageViewSet, basename="image")  # For community feed image details
router.register(r"comments", CommentViewSet, basename="comment")
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    # Health check endpoint
    path("health", HealthCheckView.as_view(), name="health"),
    # Authentication endpoints
    path("auth/google/login/", GoogleLoginView.as_view(), name="google_login"),
    path("auth/google/callback/", GoogleCallbackView.as_view(), name="google_callback"),
    path("auth/logout/", LogoutView.as_view(), name="logout"),
    path("auth/me/", MeView.as_view(), name="me"),
    path("auth/token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Webhook endpoints (AI servers → Backend)
    path("webhooks/training/progress", webhook.training_progress, name="webhook_training_progress"),
    path("webhooks/training/complete", webhook.training_complete, name="webhook_training_complete"),
    path("webhooks/training/failed", webhook.training_failed, name="webhook_training_failed"),
    path("webhooks/inference/progress", webhook.inference_progress, name="webhook_inference_progress"),
    path("webhooks/inference/complete", webhook.inference_complete, name="webhook_inference_complete"),
    path("webhooks/inference/failed", webhook.inference_failed, name="webhook_inference_failed"),
    # Include router URLs for ViewSets
    path("", include(router.urls)),
]
