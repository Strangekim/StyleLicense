"""
Django management command to check recent users.
"""
from django.core.management.base import BaseCommand
from app.models import User


class Command(BaseCommand):
    """Check recent users in database."""

    help = "Check recent users in database"

    def handle(self, *args, **options):
        """Execute command."""
        self.stdout.write("\n=== Recent Users (Last 10) ===\n")

        users = User.objects.all().order_by('-created_at')[:10]

        if not users:
            self.stdout.write(self.style.WARNING("No users found in database!"))
            return

        for user in users:
            self.stdout.write(f"\nID: {user.id}")
            self.stdout.write(f"Username: {user.username}")
            self.stdout.write(f"Email: {user.email}")
            self.stdout.write(f"Provider: {user.provider}")
            self.stdout.write(f"Provider User ID: {user.provider_user_id}")
            if user.profile_image:
                self.stdout.write(f"Profile Image: {user.profile_image[:80]}...")
            else:
                self.stdout.write("Profile Image: None")
            self.stdout.write(f"Token Balance: {user.token_balance}")
            self.stdout.write(f"Created At: {user.created_at}")
            self.stdout.write("-" * 70)

        total = User.objects.count()
        self.stdout.write(self.style.SUCCESS(f"\nTotal users in database: {total}"))

        # Check for users created in last hour
        from django.utils import timezone
        from datetime import timedelta

        one_hour_ago = timezone.now() - timedelta(hours=1)
        recent_users = User.objects.filter(created_at__gte=one_hour_ago).count()

        self.stdout.write(self.style.SUCCESS(f"Users created in last hour: {recent_users}"))
