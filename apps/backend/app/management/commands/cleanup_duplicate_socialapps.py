import os
from django.core.management.base import BaseCommand
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

class Command(BaseCommand):
    help = 'Remove duplicate Google SocialApps and keep only one.'

    def handle(self, *args, **options):
        client_id = os.getenv('GOOGLE_CLIENT_ID')
        secret = os.getenv('GOOGLE_CLIENT_SECRET')

        if not client_id or not secret:
            self.stdout.write(self.style.ERROR('GOOGLE_CLIENT_ID and GOOGLE_CLIENT_SECRET environment variables must be set.'))
            return

        try:
            site = Site.objects.get(id=1)
        except Site.DoesNotExist:
            self.stdout.write(self.style.ERROR('Site with id=1 does not exist.'))
            return

        # Get all Google SocialApps
        google_apps = SocialApp.objects.filter(provider='google')
        count = google_apps.count()

        self.stdout.write(f"Found {count} Google SocialApp(s)")

        if count == 0:
            # No SocialApp exists, create one
            social_app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id=client_id,
                secret=secret,
            )
            social_app.sites.set([site])
            self.stdout.write(self.style.SUCCESS(f"Created new Google SocialApp for site '{site.domain}'"))

        elif count == 1:
            # Only one exists, update it
            social_app = google_apps.first()
            social_app.name = 'Google'
            social_app.client_id = client_id
            social_app.secret = secret
            social_app.save()
            social_app.sites.set([site])
            self.stdout.write(self.style.SUCCESS(f"Updated existing Google SocialApp for site '{site.domain}'"))

        else:
            # Multiple exist, delete all and create one new
            self.stdout.write(self.style.WARNING(f"Deleting {count} duplicate SocialApps..."))
            google_apps.delete()

            social_app = SocialApp.objects.create(
                provider='google',
                name='Google',
                client_id=client_id,
                secret=secret,
            )
            social_app.sites.set([site])
            self.stdout.write(self.style.SUCCESS(f"Deleted duplicates and created new Google SocialApp for site '{site.domain}'"))
