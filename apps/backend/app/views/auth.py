"""
Authentication views for Google OAuth and session management.
"""
import logging
from django.contrib.auth import logout
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator

from app.services import TokenService

logger = logging.getLogger(__name__)


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
    Grant 100 token welcome bonus to new users.
    Enhanced with error handling to not break OAuth flow.
    """
    logger.info(f"[WelcomeBonus] Signal triggered for user {user.id} ({user.username})")

    try:
        from app.models import Transaction

        # Check if bonus already granted (idempotent)
        existing_bonus = Transaction.objects.filter(
            receiver=user,
            transaction_type='purchase',
            memo__icontains='Welcome bonus'
        ).exists()

        if existing_bonus:
            logger.info(f"[WelcomeBonus] Already granted to user {user.id}")
            return

        # Grant 100 tokens
        TokenService.add_tokens(
            user_id=user.id,
            amount=100,
            reason="Welcome bonus for new user",
            transaction_type="purchase",
        )

        logger.info(f"[WelcomeBonus] Successfully granted 100 tokens to user {user.id}")

    except Exception as e:
        # CRITICAL: Don't fail OAuth flow if welcome bonus fails
        # Just log the error and continue
        logger.error(
            f"[WelcomeBonus] Failed for user {user.id}: {e}",
            exc_info=True
        )
        # OAuth login will still succeed even if this fails


# Connect the welcome bonus signal
from allauth.account.signals import user_signed_up

user_signed_up.connect(grant_welcome_bonus)
