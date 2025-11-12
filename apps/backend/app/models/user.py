from django.contrib.auth.models import (
    AbstractBaseUser,
    BaseUserManager,
    PermissionsMixin,
)
from django.db import models
from django.utils import timezone


class UserManager(BaseUserManager):
    """Custom user manager for User model.

    Note: Password authentication is disabled (OAuth only).
    """

    def create_user(
        self,
        username,
        email,
        provider="google",
        provider_user_id=None,
        **extra_fields,
    ):
        """Create and save a regular user (OAuth only)."""
        if not username:
            raise ValueError("The Username field must be set")
        if not email:
            raise ValueError("The Email field must be set")

        email = self.normalize_email(email)
        user = self.model(
            username=username,
            email=email,
            provider=provider,
            provider_user_id=provider_user_id or username,
            **extra_fields,
        )
        # No password - OAuth only
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, **extra_fields):
        """Create and save a superuser.

        Note: Superuser also uses OAuth. For Django admin access,
        use django-allauth Google OAuth with superuser account.
        """
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", "admin")

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(username, email, **extra_fields)


class User(AbstractBaseUser, PermissionsMixin):
    """Custom user model for authentication via Google OAuth.

    Note: This model uses AbstractBaseUser for django-allauth compatibility,
    but password authentication is disabled (OAuth only).
    """

    ROLE_CHOICES = [
        ("user", "User"),
        ("artist", "Artist"),
        ("admin", "Admin"),
    ]

    PROVIDER_CHOICES = [
        ("google", "Google"),
    ]

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Disable password field (OAuth only)
    password = None

    # Basic fields
    username = models.CharField(max_length=50, unique=True)
    email = models.EmailField(max_length=255, unique=True)
    provider = models.CharField(
        max_length=30, choices=PROVIDER_CHOICES, default="google"
    )
    provider_user_id = models.CharField(max_length=255)
    profile_image = models.TextField(null=True, blank=True)

    # Role and permissions
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default="user")

    # Token balance
    token_balance = models.BigIntegerField(default=0)

    # Profile
    bio = models.TextField(null=True, blank=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "username"
    REQUIRED_FIELDS = ["email"]  # Required for createsuperuser command

    class Meta:
        db_table = "users"
        constraints = [
            models.UniqueConstraint(
                fields=["provider", "provider_user_id"], name="unique_provider_user"
            ),
            models.CheckConstraint(
                check=models.Q(token_balance__gte=0), name="token_balance_non_negative"
            ),
        ]
        indexes = [
            models.Index(
                fields=["provider", "provider_user_id"],
                name="idx_users_provider_userid",
            ),
            models.Index(
                fields=["role"],
                name="idx_users_role",
                condition=models.Q(role="artist"),
            ),
        ]

    def __str__(self):
        return f"{self.username} ({self.role})"

    def set_password(self, raw_password):
        """Disabled - OAuth only authentication."""
        raise NotImplementedError("Password authentication is disabled. Use Google OAuth.")

    def check_password(self, raw_password):
        """Disabled - OAuth only authentication."""
        raise NotImplementedError("Password authentication is disabled. Use Google OAuth.")

    def save(self, *args, **kwargs):
        """Override save to ensure updated_at is set."""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)


class Artist(models.Model):
    """Artist profile model with 1:1 relationship to User."""

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Foreign key (1:1 with User)
    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="artist_profile"
    )

    # Artist-specific fields
    artist_name = models.CharField(max_length=100, null=True, blank=True)
    signature_image_url = models.TextField(null=True, blank=True)
    verified_email = models.EmailField(max_length=255, null=True, blank=True)

    # Earnings
    earned_token_balance = models.BigIntegerField(default=0)

    # Statistics (cached)
    follower_count = models.IntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "artists"
        constraints = [
            models.CheckConstraint(
                check=models.Q(earned_token_balance__gte=0),
                name="earned_token_balance_non_negative",
            ),
        ]
        indexes = [
            models.Index(fields=["user"], name="idx_artists_user_id"),
        ]

    def __str__(self):
        return f"Artist: {self.artist_name or self.user.username}"

    def save(self, *args, **kwargs):
        """Override save to ensure updated_at is set."""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
