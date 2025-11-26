"""
Authentication views for custom Google OAuth and session management.
"""
import logging
import secrets
import requests
import time
from urllib.parse import urlencode
from django.conf import settings
from django.contrib.auth import login, logout
from django.core import signing
from django.http import JsonResponse, HttpResponseRedirect
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import transaction

from app.models import User
from app.services import TokenService

logger = logging.getLogger(__name__)


class GoogleLoginView(View):
    """
    Initiates Google OAuth2 flow by redirecting to Google's authorization URL.
    """

    def get(self, request):
        """Redirect to Google OAuth authorization page."""
        # Generate signed state token for CSRF protection (no session needed)
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
    Handles OAuth callback, exchanges code for tokens, creates/gets user, grants welcome bonus.
    """

    @method_decorator(csrf_exempt)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request):
        """Handle OAuth callback from Google."""
        # Get authorization code and state from query params
        code = request.GET.get('code')
        state = request.GET.get('state')
        error = request.GET.get('error')

        # Check for OAuth errors
        if error:
            logger.error(f"[OAuth] Google returned error: {error}")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=oauth_failed")

        if not code:
            logger.error("[OAuth] No authorization code received")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=no_code")

        # Verify signed state token to prevent CSRF (no session needed)
        if not state:
            logger.error("[OAuth] No state parameter received")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=no_state")

        try:
            # Verify signature and check max_age (10 minutes)
            state_data = signing.loads(state, max_age=600)
            logger.info(f"[OAuth] State verified successfully: {state_data.get('random', '')[:10]}...")
        except signing.SignatureExpired:
            logger.error("[OAuth] State token expired (>10 minutes old)")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=state_expired")
        except signing.BadSignature:
            logger.error(f"[OAuth] Invalid state signature: {state[:20]}...")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=invalid_state")
        except Exception as e:
            logger.error(f"[OAuth] State verification error: {e}")
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=state_error")

        try:
            # Exchange authorization code for access token
            logger.info("[OAuth] Exchanging authorization code for access token")
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

            if token_response.status_code != 200:
                logger.error(f"[OAuth] Token exchange failed: {token_response.status_code} - {token_response.text}")
                return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=token_exchange_failed")

            token_data = token_response.json()
            access_token = token_data.get('access_token')

            if not access_token:
                logger.error("[OAuth] No access token in response")
                return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=no_access_token")

            # Get user info from Google
            logger.info("[OAuth] Fetching user info from Google")
            userinfo_response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                headers={'Authorization': f'Bearer {access_token}'},
                timeout=10,
            )

            if userinfo_response.status_code != 200:
                logger.error(f"[OAuth] Userinfo fetch failed: {userinfo_response.status_code}")
                return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=userinfo_failed")

            userinfo = userinfo_response.json()
            logger.info(f"[OAuth] Received user info: email={userinfo.get('email')}, id={userinfo.get('id')}")

            # Get or create user
            user = self._get_or_create_user(userinfo)

            # Log the user in (create session)
            login(request, user, backend='django.contrib.auth.backends.ModelBackend')
            logger.info(f"[OAuth] User logged in: id={user.id}, username={user.username}")

            # Clear OAuth state from session
            request.session.pop('oauth_state', None)

            # Redirect to frontend
            redirect_url = f"{settings.FRONTEND_URL}/"
            logger.info(f"[OAuth] Redirecting to frontend: {redirect_url}")
            return HttpResponseRedirect(redirect_url)

        except requests.RequestException as e:
            logger.error(f"[OAuth] Request error: {e}", exc_info=True)
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=network_error")
        except Exception as e:
            logger.error(f"[OAuth] Unexpected error: {e}", exc_info=True)
            return HttpResponseRedirect(f"{settings.FRONTEND_URL}/?error=server_error")

    @transaction.atomic
    def _get_or_create_user(self, userinfo):
        """
        Get existing user or create new user from Google userinfo.
        Grants welcome bonus to new users.
        """
        google_id = userinfo.get('id')
        email = userinfo.get('email')
        profile_image = userinfo.get('picture')

        # Try to find existing user by Google ID
        try:
            user = User.objects.get(provider='google', provider_user_id=google_id)
            logger.info(f"[OAuth] Found existing user: id={user.id}")
            return user
        except User.DoesNotExist:
            pass

        # Try to find by email
        try:
            user = User.objects.get(email=email)
            # Link Google account to existing user
            user.provider = 'google'
            user.provider_user_id = google_id
            if profile_image:
                user.profile_image = profile_image
            user.save()
            logger.info(f"[OAuth] Linked Google to existing user: id={user.id}")
            return user
        except User.DoesNotExist:
            pass

        # Create new user
        logger.info(f"[OAuth] Creating new user for {email}")

        # Generate username from email
        email_prefix = email.split('@')[0] if email else 'user'
        username = self._generate_unique_username(email_prefix[:45])

        user = User.objects.create(
            username=username,
            email=email,
            provider='google',
            provider_user_id=google_id,
            profile_image=profile_image,
            role='user',
            is_active=True,
        )

        logger.info(f"[OAuth] Created new user: id={user.id}, username={username}")

        # Grant welcome bonus
        try:
            self._grant_welcome_bonus(user)
        except Exception as e:
            # Don't fail login if welcome bonus fails
            logger.error(f"[OAuth] Welcome bonus failed for user {user.id}: {e}", exc_info=True)

        return user

    def _generate_unique_username(self, base_username):
        """Generate unique username from base, max 50 chars."""
        username = base_username[:50]
        counter = 1

        while User.objects.filter(username=username).exists():
            suffix = f"_{counter}"
            max_base_len = 50 - len(suffix)
            username = f"{base_username[:max_base_len]}{suffix}"
            counter += 1

            if counter > 999:
                # Fallback: use timestamp for uniqueness
                import time
                timestamp = str(int(time.time()))[-6:]
                username = f"{base_username[:43]}_{timestamp}"
                logger.warning(f"[OAuth] Too many username collisions, using timestamp: {username}")
                break

        logger.info(f"[OAuth] Generated unique username: {username} (base: {base_username})")
        return username

    def _grant_welcome_bonus(self, user):
        """Grant 100 token welcome bonus to new users."""
        from app.models import Transaction

        # Check if bonus already granted (idempotent)
        existing_bonus = Transaction.objects.filter(
            receiver=user,
            transaction_type='purchase',
            memo__icontains='Welcome bonus'
        ).exists()

        if existing_bonus:
            logger.info(f"[OAuth] Welcome bonus already granted to user {user.id}")
            return

        # Grant 100 tokens
        TokenService.add_tokens(
            user_id=user.id,
            amount=100,
            reason="Welcome bonus for new user",
            transaction_type="purchase",
        )

        logger.info(f"[OAuth] Granted 100 tokens welcome bonus to user {user.id}")


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
