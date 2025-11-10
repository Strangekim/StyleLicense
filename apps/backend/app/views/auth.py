"""
Authentication views for Google OAuth and session management.
"""
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from app.models import User
from app.services import TokenService


class GoogleCallbackView(View):
    """
    Google OAuth2 callback view.
    Handles OAuth callback, creates/gets user, grants welcome bonus.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        """Handle OAuth callback from Google."""
        # In production, this would process the OAuth code
        # For now, we'll return a simple response
        # The actual OAuth flow will be handled by django-allauth

        return JsonResponse(
            {
                "message": "OAuth callback endpoint. Use allauth URLs for actual OAuth flow.",
                "redirect_to_login": "/api/auth/google/login/",
            }
        )


class LogoutView(View):
    """Logout view to clear session."""

    def post(self, request):
        """Clear user session."""
        if request.user.is_authenticated:
            logout(request)
            return JsonResponse({"message": "Logged out successfully"}, status=200)
        return JsonResponse({"error": "Not authenticated"}, status=401)


class MeView(View):
    """Get current authenticated user information."""

    def get(self, request):
        """Return current user data or 401 if not authenticated."""
        if not request.user.is_authenticated:
            return JsonResponse({"error": "Not authenticated"}, status=401)

        user = request.user

        # Get artist profile if exists
        artist_profile = None
        if hasattr(user, "artist_profile"):
            artist_profile = {
                "artist_name": user.artist_profile.artist_name,
                "signature_image_url": user.artist_profile.signature_image_url,
                "earned_token_balance": user.artist_profile.earned_token_balance,
                "follower_count": user.artist_profile.follower_count,
            }

        return JsonResponse(
            {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "provider": user.provider,
                "profile_image": user.profile_image,
                "role": user.role,
                "token_balance": user.token_balance,
                "bio": user.bio,
                "is_active": user.is_active,
                "created_at": user.created_at.isoformat(),
                "artist_profile": artist_profile,
            },
            status=200,
        )


def grant_welcome_bonus(sender, request, user, **kwargs):
    """
    Signal handler to grant welcome bonus on first login.
    This should be connected to allauth's user_signed_up signal.
    """
    try:
        # Check if this is a new user (first login)
        # We check if there are any transactions for this user
        from app.models import Transaction

        has_transactions = Transaction.objects.filter(receiver=user).exists()

        if not has_transactions:
            # Grant welcome bonus
            TokenService.add_tokens(
                user_id=user.id,
                amount=100,
                reason="Welcome bonus for new user",
                transaction_type="purchase",  # System grant
            )
    except Exception as e:
        # Log error but don't fail the login
        print(f"Error granting welcome bonus: {e}")


# Connect the welcome bonus signal
from allauth.account.signals import user_signed_up

user_signed_up.connect(grant_welcome_bonus)
