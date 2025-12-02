"""
Authentication views for custom Google OAuth and token-based authentication.
"""
import logging
import secrets
import requests
import time
from urllib.parse import urlencode, urlunparse, urlparse
from django.conf import settings
from django.contrib.auth import logout
from django.core import signing
from django.http import JsonResponse, HttpResponseRedirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken

from app.models import User
from app.services import TokenService

logger = logging.getLogger(__name__)


class GoogleLoginView(View):
    """
    Initiates Google OAuth2 flow by redirecting to Google's authorization URL.
    """

    def get(self, request):
        """Redirect to Google OAuth authorization page."""
        # Generate signed state token for CSRF protection
        random_value = secrets.token_urlsafe(16)
        timestamp = int(time.time())
        state_data = {'random': random_value, 'timestamp': timestamp}

        # Sign the state using Django's signing module (max_age=600 = 10 minutes)
        state = signing.dumps(state_data)

        # Build Google OAuth URL
        params = {
            'client_id': settings.GOOGLE_CLIENT_ID,
            'redirect_uri': settings.GOOGLE_REDIRECT_URI,
            'response_type': 'code',
            'scope': 'openid email profile',
            'state': state,
            'access_type': 'online',
        }

        auth_url = f"https://accounts.google.com/o/oauth2/v2/auth?{urlencode(params)}"

        logger.info(f"[OAuth] Redirecting to Google OAuth: state={state[:20]}...")
        return HttpResponseRedirect(auth_url)


class GoogleCallbackView(View):
    """
    Google OAuth2 callback view.
    Handles OAuth callback, gets/creates a user, and returns JWT tokens.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        """Handle OAuth callback from Google."""
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')

        if error:
            logger.error(f"[OAuth] Google returned error: {error}")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/login?error=oauth_failed")

        if not code:
            logger.error("[OAuth] No authorization code received")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/login?error=no_code")

        if not state:
            logger.error("[OAuth] No state parameter received")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/login?error=no_state")

        try:
            state_data = signing.loads(state, max_age=600)
            logger.info(f"[OAuth] State verified successfully: {state_data.get('random', '')[:10]}...")
        except (signing.SignatureExpired, signing.BadSignature) as e:
            logger.error(f"[OAuth] State verification failed: {e}")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/login?error=invalid_state")

        try:
            # Exchange authorization code for access token
            token_response = requests.post(
                'https://oauth2.googleapis.com/token',
                data={
                    'code': code,
                    'client_id': settings.GOOGLE_CLIENT_ID,
                    'client_secret': settings.GOOGLE_CLIENT_SECRET,
                    'redirect_uri': settings.GOOGLE_REDIRECT_URI,
                    'grant_type': 'authorization_code',
                },
                timeout=10,
            )
            token_response.raise_for_status()
            token_data = token_response.json()
            google_access_token = token_data.get('access_token')

            # Get user info from Google
            userinfo_response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {google_access_token}'},
                timeout=10,
            )
            userinfo_response.raise_for_status()
            userinfo = userinfo_response.json()
            logger.info(f"[OAuth] Received user info: email={userinfo.get('email')}")

            # Get or create user
            user = self._get_or_create_user(userinfo)

            # Generate JWT tokens
            refresh = RefreshToken.for_user(user)
            access_token = str(refresh.access_token)
            refresh_token = str(refresh)
            
            logger.info(f"[OAuth] Generated JWT for user {user.id}")

            # Redirect to frontend callback with tokens
            redirect_url_parts = list(urlparse(f"{settings.FRONTEND_URL}/auth/callback"))
            query_params = {
                'access_token': access_token,
                'refresh_token': refresh_token,
            }
            redirect_url_parts[4] = urlencode(query_params)
            redirect_url = urlunparse(redirect_url_parts)
            
            logger.info(f"[OAuth] Redirecting to frontend with tokens: {redirect_url}")
            return HttpResponseRedirect(redirect_url)

        except requests.RequestException as e:
            logger.error(f"[OAuth] Request error: {e}", exc_info=True)
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/login?error=network_error")
        except Exception as e:
            logger.error(f"[OAuth] Unexpected error in callback: {e}", exc_info=True)
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/login?error=server_error")

    @transaction.atomic
    def _get_or_create_user(self, userinfo):
        """
        Get existing user or create a new one from Google userinfo.
        """
        google_id = userinfo.get('id')
        email = userinfo.get('email')

        if not email:
            raise ValueError("Email not provided by Google")

        try:
            # Try to find existing user by Google ID or email
            user = User.objects.get(email=email)
            if not user.provider_user_id:
                user.provider = 'google'
                user.provider_user_id = google_id
                user.save()
            logger.info(f"[OAuth] Found existing user: id={user.id}")
            return user
        except User.DoesNotExist:
            # Create new user
            logger.info(f"[OAuth] Creating new user for {email}")
            email_prefix = email.split('@')[0]
            username = self._generate_unique_username(email_prefix)

            user = User.objects.create_user(
                username=username,
                email=email,
                provider='google',
                provider_user_id=google_id,
                profile_image=userinfo.get('picture'),
            )
            logger.info(f"[OAuth] Created new user: id={user.id}, username={username}")
            
            # Grant welcome bonus
            self._grant_welcome_bonus(user)
            return user

    def _generate_unique_username(self, base_username):
        """Generate a unique username to avoid collisions."""
        username = base_username[:130]
        counter = 1
        while User.objects.filter(username=username).exists():
            suffix = f"_{counter}"
            username = f"{base_username[:130 - len(suffix)]}{suffix}"
            counter += 1
        return username

    def _grant_welcome_bonus(self, user):
        """Grants a welcome bonus to new users."""
        TokenService.add_tokens(
            user_id=user.id,
            amount=100,
            reason="Welcome bonus for new user",
            transaction_type="purchase",
        )
        logger.info(f"[OAuth] Granted 100 tokens welcome bonus to user {user.id}")


class LogoutView(View):
    """Logout view for token-based auth."""

    def post(self, request):
        """
        Frontend should handle token removal. This is just a confirmation endpoint.
        For a more secure implementation, a token blacklist should be used.
        """
        return JsonResponse({"message": "Logout successful. Please clear tokens on client-side."}, status=200)


class MeView(APIView):
    """Get current authenticated user information (JWT-based)."""
    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return current user data or 401 if not authenticated via JWT."""
        logger.info(f"[Auth] MeView received Authorization header: {request.headers.get('Authorization')}")
        logger.info(f"[Auth] MeView authenticated user: {request.user.username} (IsAuthenticated: {request.user.is_authenticated})")

        user = request.user
        artist_profile = None
        if hasattr(user, "artist_profile"):
            artist_profile = {
                "artist_name": user.artist_profile.artist_name,
                "signature_image_url": user.artist_profile.signature_image_url,
                "earned_token_balance": user.artist_profile.earned_token_balance,
                "follower_count": user.artist_profile.follower_count,
            }

        return Response({
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
        }, status=200)
