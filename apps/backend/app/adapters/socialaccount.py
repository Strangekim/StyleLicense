"""
Custom adapter for django-allauth to handle OAuth redirects and user creation.
"""
import logging
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings

logger = logging.getLogger(__name__)


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    """
    Custom social account adapter with comprehensive logging and user creation.
    """

    def pre_social_login(self, request, sociallogin):
        """Log OAuth attempt and link to existing user if email matches."""
        logger.info(
            f"[OAuth] Pre-login: provider={sociallogin.account.provider}, "
            f"uid={sociallogin.account.uid}, "
            f"is_existing={sociallogin.is_existing}"
        )

        # Link to existing user if email matches (prevents duplicate email errors)
        if not sociallogin.is_existing and sociallogin.email_addresses:
            email = sociallogin.email_addresses[0].email
            logger.info(f"[OAuth] Checking for existing user with email: {email}")

            try:
                from app.models import User
                existing_user = User.objects.get(email=email)

                # Connect this OAuth provider to existing user
                sociallogin.connect(request, existing_user)
                logger.info(f"[OAuth] Linked to existing user: {existing_user.id}")

            except User.DoesNotExist:
                logger.info(f"[OAuth] New user - email not found")
            except Exception as e:
                logger.error(f"[OAuth] Error checking existing user: {e}", exc_info=True)

        super().pre_social_login(request, sociallogin)

    def populate_user(self, request, sociallogin, data):
        """Override to extract profile image and generate email-based username."""
        logger.info(f"[OAuth] Populating user from {sociallogin.account.provider}")
        logger.info(f"[OAuth] OAuth data: {data}")

        # Call parent to get base user object
        user = super().populate_user(request, sociallogin, data)

        # Extract profile image from Google OAuth
        if sociallogin.account.provider == 'google':
            extra_data = sociallogin.account.extra_data
            profile_image = extra_data.get('picture')

            if profile_image:
                user.profile_image = profile_image
                logger.info(f"[OAuth] Set profile_image from Google")

        # Generate username from email prefix (user@example.com -> "user")
        if user.email:
            email_prefix = user.email.split('@')[0]
            # Ensure max 50 chars and generate unique username
            user.username = self._generate_unique_username(email_prefix[:45])
            logger.info(f"[OAuth] Generated username from email: {user.username}")
        else:
            logger.warning(f"[OAuth] No email - using default username: {user.username}")

        # Set provider_user_id from Google UID
        user.provider = sociallogin.account.provider
        user.provider_user_id = sociallogin.account.uid

        logger.info(
            f"[OAuth] User populated: username={user.username}, "
            f"email={user.email}, provider_user_id={user.provider_user_id}"
        )

        return user

    def save_user(self, request, sociallogin, form=None):
        """Override to add logging and error handling."""
        logger.info(f"[OAuth] Attempting to save user")

        try:
            user = super().save_user(request, sociallogin, form)
            logger.info(f"[OAuth] User saved successfully: id={user.id}, username={user.username}")
            return user

        except Exception as e:
            logger.error(f"[OAuth] Failed to save user: {e}", exc_info=True)
            raise

    def get_login_redirect_url(self, request):
        """Redirect to frontend URL after successful OAuth login."""
        frontend_url = getattr(settings, 'FRONTEND_URL', None)

        if not frontend_url:
            logger.error("[OAuth] FRONTEND_URL not configured in settings!")
            frontend_url = 'http://localhost:5173'

        redirect_url = f"{frontend_url}/"
        logger.info(f"[OAuth] Redirecting to: {redirect_url}")

        return redirect_url

    def _generate_unique_username(self, base_username):
        """Generate unique username from base, max 50 chars."""
        from app.models import User

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
