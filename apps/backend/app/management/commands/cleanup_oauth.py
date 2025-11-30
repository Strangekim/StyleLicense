"""
Django management command to cleanup and setup OAuth
"""
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp
import os


class Command(BaseCommand):
    help = 'Cleanup duplicate SocialApps and setup OAuth correctly'

    def handle(self, *args, **options):
        # Step 1: Update Site
        try:
            site = Site.objects.get(id=1)
            old_domain = site.domain
            # Use SITE_DOMAIN env var or default to Firebase Hosting domain
            site_domain = os.getenv('SITE_DOMAIN', 'noted-sled-478700-r3.web.app')
            site.domain = site_domain
            site.name = 'Style License'
            site.save()
            self.stdout.write(
                self.style.SUCCESS(
                    f"[OAuth Setup] Updated Site to {site.domain}"
                )
            )
        except Site.DoesNotExist:
            self.stdout.write(
                self.style.ERROR('Site with id=1 does not exist')
            )
            return

        # Step 2: Delete all Google SocialApps
        deleted_count = SocialApp.objects.filter(provider='google').delete()[0]
        self.stdout.write(f"Deleted {deleted_count} existing Google SocialApp(s)")

        # Step 3: Create new SocialApp
        client_id = os.getenv('GOOGLE_CLIENT_ID', '')
        secret = os.getenv('GOOGLE_CLIENT_SECRET', '')

        if not client_id or not secret:
            self.stdout.write(
                self.style.ERROR(
                    'GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET must be set'
                )
            )
            return

        social_app = SocialApp.objects.create(
            provider='google',
            name='Google',
            client_id=client_id,
            secret=secret,
        )
        social_app.sites.add(site)

        self.stdout.write(
            self.style.SUCCESS(
                f"Created new Google SocialApp for {site.domain}"
            )
        )

        # Verify
        self.stdout.write("\nVerification:")
        self.stdout.write(f"  Site: {site.domain}")
        self.stdout.write(f"  Provider: {social_app.provider}")
        self.stdout.write(f"  Client ID: {social_app.client_id[:20]}...")
        self.stdout.write(f"  Total Google SocialApps: {SocialApp.objects.filter(provider='google').count()}")
