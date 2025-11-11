"""
Custom permissions for Style License API.

Provides role-based and object-level permissions:
- IsArtist: Only artists can perform action
- IsOwnerOrReadOnly: Only owner can modify, everyone can read
- IsOwner: Only owner can access
"""
from rest_framework import permissions


class IsArtist(permissions.BasePermission):
    """
    Permission check for artist role.

    Only allows access to users with role='artist'.
    """

    message = "Only artists can perform this action."

    def has_permission(self, request, view):
        """Check if user is authenticated and has artist role."""
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role == "artist"
        )


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    Object-level permission: only owner can modify, everyone can read.

    - SAFE_METHODS (GET, HEAD, OPTIONS): allowed for everyone
    - Modification methods (POST, PUT, PATCH, DELETE): only owner
    """

    def has_object_permission(self, request, view, obj):
        """Check if user can access the object."""
        # Allow read permissions for everyone
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions only for owner
        # Check if object has 'artist' or 'user' attribute
        owner = getattr(obj, "artist", getattr(obj, "user", None))
        return owner == request.user


class IsOwner(permissions.BasePermission):
    """
    Object-level permission: only owner can access.

    Used for sensitive operations like viewing private data,
    modifying settings, etc.
    """

    message = "You do not have permission to access this resource."

    def has_object_permission(self, request, view, obj):
        """Check if user is the owner."""
        # Check if object has 'artist' or 'user' attribute
        owner = getattr(obj, "artist", getattr(obj, "user", None))
        return owner == request.user
