"""
URL configuration for app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from app.views.auth import LogoutView, MeView, GoogleCallbackView
from app.views.health import HealthCheckView
from app.views.style import StyleViewSet
from app.views.token import TokenViewSet
from app.views.tag import TagViewSet
from app.views.notification import NotificationViewSet
from app.views.community import (
    CommunityViewSet,
    GenerationViewSet,
    CommentViewSet,
    UserViewSet,
)

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r"models", StyleViewSet, basename="style")
router.register(r"tokens", TokenViewSet, basename="token")
router.register(r"tags", TagViewSet, basename="tag")
router.register(r"notifications", NotificationViewSet, basename="notification")
router.register(r"community", CommunityViewSet, basename="community")
router.register(r"images", GenerationViewSet, basename="image")
router.register(r"comments", CommentViewSet, basename="comment")
router.register(r"users", UserViewSet, basename="user")

urlpatterns = [
    # Health check endpoint
    path("health", HealthCheckView.as_view(), name="health"),
    # Authentication endpoints
    path("auth/logout", LogoutView.as_view(), name="logout"),
    path("auth/me", MeView.as_view(), name="me"),
    path("auth/google/callback", GoogleCallbackView.as_view(), name="google_callback"),
    # Include allauth URLs for OAuth flow
    path("auth/", include("allauth.urls")),
    # Include router URLs for ViewSets
    path("", include(router.urls)),
]
