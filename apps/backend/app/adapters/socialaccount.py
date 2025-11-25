"""
Custom adapter for django-allauth to handle OAuth redirects to frontend.
"""
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter to redirect to frontend after OAuth login.
    """

    def get_login_redirect_url(self, request):
        """
        Override to redirect to frontend URL after successful OAuth login.
        """
        # Get the frontend URL from settings
        frontend_url = getattr(settings, 'FRONTEND_URL', 'http://localhost:5173')

        # Return the frontend homepage
        return f"{frontend_url}/"
