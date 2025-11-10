"""
URL configuration for app.
"""
from django.urls import path, include
from app.views.auth import LogoutView, MeView, GoogleCallbackView

urlpatterns = [
    # Authentication endpoints
    path('auth/logout', LogoutView.as_view(), name='logout'),
    path('auth/me', MeView.as_view(), name='me'),
    path('auth/google/callback', GoogleCallbackView.as_view(), name='google_callback'),

    # Include allauth URLs for OAuth flow
    path('auth/', include('allauth.urls')),
]
