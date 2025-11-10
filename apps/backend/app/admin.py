from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import (
    User,
    Artist,
    Transaction,
    Purchase,
    Style,
    Artwork,
    Generation,
    Tag,
    StyleTag,
    ArtworkTag,
    GenerationTag,
    Follow,
    Like,
    Comment,
    Notification,
)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    """Admin for User model."""

    list_display = (
        "id",
        "username",
        "provider",
        "role",
        "token_balance",
        "is_active",
        "created_at",
    )
    list_filter = ("role", "is_active", "provider")
    search_fields = ("username", "provider_user_id")
    ordering = ("-created_at",)

    fieldsets = (
        (None, {"fields": ("username", "password")}),
        ("OAuth Info", {"fields": ("provider", "provider_user_id", "profile_image")}),
        ("Profile", {"fields": ("role", "token_balance", "bio")}),
        (
            "Permissions",
            {
                "fields": (
                    "is_active",
                    "is_staff",
                    "is_superuser",
                    "groups",
                    "user_permissions",
                )
            },
        ),
        ("Important dates", {"fields": ("last_login", "created_at", "updated_at")}),
    )
    readonly_fields = ("created_at", "updated_at")


@admin.register(Artist)
class ArtistAdmin(admin.ModelAdmin):
    """Admin for Artist model."""

    list_display = (
        "id",
        "user",
        "artist_name",
        "earned_token_balance",
        "follower_count",
        "created_at",
    )
    search_fields = ("artist_name", "user__username")
    readonly_fields = ("created_at", "updated_at")


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    """Admin for Transaction model."""

    list_display = (
        "id",
        "sender",
        "receiver",
        "amount",
        "transaction_type",
        "status",
        "created_at",
    )
    list_filter = ("transaction_type", "status")
    search_fields = ("sender__username", "receiver__username")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)


@admin.register(Purchase)
class PurchaseAdmin(admin.ModelAdmin):
    """Admin for Purchase model."""

    list_display = ("id", "buyer", "amount_tokens", "status", "provider", "created_at")
    list_filter = ("status", "provider")
    search_fields = ("buyer__username", "provider_payment_key", "provider_order_id")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Style)
class StyleAdmin(admin.ModelAdmin):
    """Admin for Style model."""

    list_display = (
        "id",
        "name",
        "artist",
        "training_status",
        "generation_cost_tokens",
        "usage_count",
        "is_active",
    )
    list_filter = ("training_status", "license_type", "is_active", "is_flagged")
    search_fields = ("name", "artist__username")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Artwork)
class ArtworkAdmin(admin.ModelAdmin):
    """Admin for Artwork model."""

    list_display = ("id", "style", "is_valid", "created_at")
    list_filter = ("is_valid",)
    search_fields = ("style__name",)
    readonly_fields = ("created_at",)


@admin.register(Generation)
class GenerationAdmin(admin.ModelAdmin):
    """Admin for Generation model."""

    list_display = (
        "id",
        "user",
        "style",
        "status",
        "consumed_tokens",
        "is_public",
        "like_count",
        "created_at",
    )
    list_filter = ("status", "is_public")
    search_fields = ("user__username", "style__name")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    """Admin for Tag model."""

    list_display = ("id", "name", "usage_count", "is_active", "created_at")
    list_filter = ("is_active",)
    search_fields = ("name",)
    readonly_fields = ("created_at",)


@admin.register(StyleTag)
class StyleTagAdmin(admin.ModelAdmin):
    """Admin for StyleTag model."""

    list_display = ("style", "tag", "sequence", "created_at")
    search_fields = ("style__name", "tag__name")
    readonly_fields = ("created_at",)


@admin.register(ArtworkTag)
class ArtworkTagAdmin(admin.ModelAdmin):
    """Admin for ArtworkTag model."""

    list_display = ("artwork", "tag", "sequence", "created_at")
    search_fields = ("tag__name",)
    readonly_fields = ("created_at",)


@admin.register(GenerationTag)
class GenerationTagAdmin(admin.ModelAdmin):
    """Admin for GenerationTag model."""

    list_display = ("generation", "tag", "sequence", "created_at")
    search_fields = ("tag__name",)
    readonly_fields = ("created_at",)


@admin.register(Follow)
class FollowAdmin(admin.ModelAdmin):
    """Admin for Follow model."""

    list_display = ("id", "follower", "following", "created_at")
    search_fields = ("follower__username", "following__username")
    readonly_fields = ("created_at",)


@admin.register(Like)
class LikeAdmin(admin.ModelAdmin):
    """Admin for Like model."""

    list_display = ("id", "user", "generation", "created_at")
    search_fields = ("user__username",)
    readonly_fields = ("created_at",)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    """Admin for Comment model."""

    list_display = ("id", "user", "generation", "parent", "like_count", "created_at")
    search_fields = ("user__username", "content")
    readonly_fields = ("created_at", "updated_at")
    ordering = ("-created_at",)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for Notification model."""

    list_display = ("id", "recipient", "actor", "type", "is_read", "created_at")
    list_filter = ("type", "is_read")
    search_fields = ("recipient__username", "actor__username")
    readonly_fields = ("created_at",)
    ordering = ("-created_at",)
