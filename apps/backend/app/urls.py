"""
URL configuration for app.
"""
from django.urls import path, include
from rest_framework.routers import DefaultRouter

from app.views.auth import LogoutView, MeView, GoogleCallbackView
from app.views.health import HealthCheckView
from app.views.style import StyleViewSet
from app.views.token import TokenViewSet

# DRF Router for ViewSets
router = DefaultRouter()
router.register(r"models", StyleViewSet, basename="style")
router.register(r"tokens", TokenViewSet, basename="token")

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
