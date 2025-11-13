"""
Create test data for development.

This script creates test users and data for API testing.
Note: OAuth only - no password authentication.
"""
import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from app.models import User, Artist, Style, Tag
from django.contrib.sites.models import Site
from allauth.socialaccount.models import SocialApp

def create_test_data():
    """Create test users, styles, and tags."""

    print("=" * 60)
    print("Creating Test Data (OAuth Only)")
    print("=" * 60)

    # 1. Create SocialApp for Google OAuth
    print("\n[1/5] Creating Google OAuth SocialApp...")
    google_client_id = os.getenv("GOOGLE_CLIENT_ID", "")
    google_client_secret = os.getenv("GOOGLE_CLIENT_SECRET", "")

    if not google_client_id or not google_client_secret:
        print("[WARNING]  Warning: GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET not set in .env")

    site = Site.objects.get_current()

    social_app, created = SocialApp.objects.get_or_create(
        provider="google",
        defaults={
            "name": "Google OAuth",
            "client_id": google_client_id,
            "secret": google_client_secret,
        }
    )

    if created:
        social_app.sites.add(site)
        print(f"[OK] Created SocialApp: {social_app.name}")
    else:
        print(f"[OK] SocialApp already exists: {social_app.name}")

    # 2. Create test users (OAuth simulation)
    print("\n[2/5] Creating test users...")

    # Artist user
    artist_user, created = User.objects.get_or_create(
        email="artist@example.com",
        defaults={
            "username": "test_artist",
            "provider": "google",
            "provider_user_id": "google-artist-12345",
            "role": "artist",
            "token_balance": 1000,
            "bio": "Test artist account for development",
            "is_active": True,
        }
    )
    if created:
        print(f"[OK] Created artist: {artist_user.email}")
    else:
        print(f"[OK] Artist already exists: {artist_user.email}")

    # Regular user
    regular_user, created = User.objects.get_or_create(
        email="user@example.com",
        defaults={
            "username": "test_user",
            "provider": "google",
            "provider_user_id": "google-user-67890",
            "role": "user",
            "token_balance": 500,
            "bio": "Test user account for development",
            "is_active": True,
        }
    )
    if created:
        print(f"[OK] Created user: {regular_user.email}")
    else:
        print(f"[OK] User already exists: {regular_user.email}")

    # 3. Create artist profile
    print("\n[3/5] Creating artist profile...")
    artist_profile, created = Artist.objects.get_or_create(
        user=artist_user,
        defaults={
            "artist_name": "Test Artist",
            "verified_email": "artist@example.com",
            "earned_token_balance": 0,
            "follower_count": 0,
        }
    )
    if created:
        print(f"[OK] Created artist profile: {artist_profile.artist_name}")
    else:
        print(f"[OK] Artist profile already exists: {artist_profile.artist_name}")

    # 4. Create test styles
    print("\n[4/5] Creating test styles...")
    style1, created = Style.objects.get_or_create(
        artist=artist_user,
        name="Watercolor Dreams",
        defaults={
            "description": "Soft watercolor painting style",
            "training_status": "completed",
            "generation_cost_tokens": 10,
            "license_type": "personal",
            "is_active": True,
        }
    )
    if created:
        print(f"[OK] Created style: {style1.name}")
    else:
        print(f"[OK] Style already exists: {style1.name}")

    style2, created = Style.objects.get_or_create(
        artist=artist_user,
        name="Digital Sketch",
        defaults={
            "description": "Hand-drawn digital sketch style",
            "training_status": "completed",
            "generation_cost_tokens": 15,
            "license_type": "commercial",
            "is_active": True,
        }
    )
    if created:
        print(f"[OK] Created style: {style2.name}")
    else:
        print(f"[OK] Style already exists: {style2.name}")

    # 5. Create test tags
    print("\n[5/5] Creating test tags...")
    tag_names = ["portrait", "landscape", "abstract", "anime", "realistic"]
    for tag_name in tag_names:
        tag, created = Tag.objects.get_or_create(
            name=tag_name,
            defaults={"is_active": True, "usage_count": 0}
        )
        if created:
            print(f"[OK] Created tag: {tag.name}")
        else:
            print(f"[OK] Tag already exists: {tag.name}")

    # Summary
    print("\n" + "=" * 60)
    print("Test Data Created Successfully!")
    print("=" * 60)
    print("\n[NOTE] Test Accounts (OAuth only):")
    print(f"   Artist: {artist_user.email} (provider_user_id: {artist_user.provider_user_id})")
    print(f"           Token Balance: {artist_user.token_balance}")
    print(f"   User:   {regular_user.email} (provider_user_id: {regular_user.provider_user_id})")
    print(f"           Token Balance: {regular_user.token_balance}")

    print("\n[WARNING]  Authentication Method:")
    print("   - Google OAuth ONLY (no password login)")
    print("   - For API testing, see POSTMAN_API_GUIDE.md")
    print("   - For frontend testing, use Google OAuth flow")

    print("\n[INFO] Data Summary:")
    print(f"   Users: {User.objects.count()}")
    print(f"   Artists: {Artist.objects.count()}")
    print(f"   Styles: {Style.objects.count()}")
    print(f"   Tags: {Tag.objects.count()}")
    print()

if __name__ == "__main__":
    try:
        create_test_data()
    except Exception as e:
        print(f"\n[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()
