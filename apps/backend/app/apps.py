from django.apps import AppConfig
import os


class AppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"
    verbose_name = "Style License"

    def ready(self):
        """Import signals when app is ready."""
        import app.signals  # noqa: F401

        # Note: OAuth setup is now handled in docker-entrypoint.sh
        # via the cleanup_oauth management command

    def setup_social_app(self):
        """Create or update Google OAuth SocialApp on startup."""
        # Only run in production or when explicitly requested
        # Avoid running during migrations or manage.py commands
        import sys
        if 'migrate' in sys.argv or 'makemigrations' in sys.argv:
            return

        try:
            from django.contrib.sites.models import Site
            from allauth.socialaccount.models import SocialApp

            client_id = os.getenv('GOOGLE_CLIENT_ID', '')
            secret = os.getenv('GOOGLE_CLIENT_SECRET', '')

            if not client_id or not secret:
                return  # Skip if credentials not configured

            # Update Site domain
            site = Site.objects.get(id=1)
            production_domain = 'stylelicense-backend-606831968092.asia-northeast3.run.app'
            if site.domain != production_domain:
                site.domain = production_domain
                site.name = 'Style License'
                site.save()
                print(f"[OAuth Setup] Updated Site to {site.domain}")

            # Delete all existing Google SocialApps to avoid duplicates
            existing_count = SocialApp.objects.filter(provider='google').count()
            if existing_count > 0:
                SocialApp.objects.filter(provider='google').delete()
                print(f"[OAuth Setup] Deleted {existing_count} existing Google SocialApp(s)")

            # Create new Google SocialApp
            social_app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id=client_id,
                secret=secret,
            )
            social_app.sites.add(site)
            print(f"[OAuth Setup] Created Google SocialApp for {site.domain}")

        except Exception as e:
            # Don't crash the app if SocialApp setup fails
            print(f"[OAuth Setup] Warning: Could not setup SocialApp: {e}")
