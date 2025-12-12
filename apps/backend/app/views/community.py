"""
Community views for Feed, Like, Comment, and Follow functionality.
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Prefetch
from django.db import transaction

from app.models import Generation, Like, Comment, Follow, User
from app.serializers.community import (
    GenerationFeedSerializer,
    GenerationDetailSerializer,
    CommentSerializer,
    CommentCreateSerializer,
    LikeToggleSerializer,
    FollowToggleSerializer,
    FollowingUserSerializer,
    UserProfileSerializer,
    UserUpdateSerializer,
)


class CommunityViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for community feed.

    list: GET /api/community/feed - Public feed of completed generations
    """

    serializer_class = GenerationFeedSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """
        Return public completed generations with optimized queries.
        """
        return (
            Generation.objects.filter(is_public=True, status="completed")
            .select_related("user", "style", "style__artist")
            .order_by("-created_at")
        )


class GenerationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for individual generation detail and interactions.

    retrieve: GET /api/images/:id - Get generation detail
    like: POST /api/images/:id/like - Toggle like
    comments: GET /api/images/:id/comments - List comments
    add_comment: POST /api/images/:id/comments - Add comment
    """

    serializer_class = GenerationDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PageNumberPagination

    def get_queryset(self):
        """
        Return completed generations that are either:
        - Public (anyone can see)
        - Private but owned by current user (owner can see their own private images)
        """
        from django.db.models import Q

        queryset = Generation.objects.filter(status="completed").select_related(
            "user", "style", "style__artist"
        )

        # If user is authenticated, show public images + their own private images
        if self.request.user.is_authenticated:
            queryset = queryset.filter(
                Q(is_public=True) | Q(user=self.request.user)
            )
        else:
            # If not authenticated, only show public images
            queryset = queryset.filter(is_public=True)

        return queryset

    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def like(self, request, pk=None):
        """
        Toggle like on a generation.

        POST /api/images/:id/like
        Response: {"is_liked": true/false, "like_count": int}
        """
        generation = self.get_object()

        with transaction.atomic():
            # Try to get existing like
            like_obj = Like.objects.filter(
                user=request.user, generation=generation
            ).first()

            if like_obj:
                # Unlike
                like_obj.delete()
                generation.like_count = max(0, generation.like_count - 1)
                generation.save(update_fields=["like_count"])
                is_liked = False
            else:
                # Like
                Like.objects.create(user=request.user, generation=generation)
                generation.like_count += 1
                generation.save(update_fields=["like_count"])
                is_liked = True

        return Response(
            LikeToggleSerializer(
                {"is_liked": is_liked, "like_count": generation.like_count}
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["get", "post"], url_path="comments")
    def comments(self, request, pk=None):
        """
        List or add comments for a generation.

        GET /api/images/:id/comments - List comments
        POST /api/images/:id/comments - Add comment
        """
        generation = self.get_object()

        if request.method == "GET":
            # List comments
            comments_queryset = (
                Comment.objects.filter(generation=generation, parent=None)
                .select_related("user")
                .order_by("created_at")
            )

            page = self.paginate_queryset(comments_queryset)
            if page is not None:
                serializer = CommentSerializer(page, many=True)
                return self.get_paginated_response(serializer.data)

            serializer = CommentSerializer(comments_queryset, many=True)
            return Response(serializer.data)

        elif request.method == "POST":
            # Add comment (requires authentication)
            if not request.user.is_authenticated:
                return Response(
                    {"error": "Authentication required"},
                    status=status.HTTP_403_FORBIDDEN,
                )

            serializer = CommentCreateSerializer(data=request.data)
            if serializer.is_valid():
                with transaction.atomic():
                    comment = serializer.save(user=request.user, generation=generation)

                    # Update comment count (only for top-level comments)
                    if not comment.parent:
                        generation.comment_count += 1
                        generation.save(update_fields=["comment_count"])

                return Response(
                    CommentSerializer(comment).data, status=status.HTTP_201_CREATED
                )

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CommentViewSet(viewsets.GenericViewSet):
    """
    ViewSet for comment management.

    destroy: DELETE /api/comments/:id - Delete comment
    """

    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]
    queryset = Comment.objects.all()

    def destroy(self, request, pk=None):
        """
        Delete a comment.

        DELETE /api/comments/:id
        Permissions: Owner or admin only
        """
        try:
            comment = Comment.objects.select_related("generation").get(pk=pk)
        except Comment.DoesNotExist:
            return Response(
                {"error": "Comment not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Check permission: owner or admin
        if comment.user != request.user and not request.user.is_staff:
            return Response(
                {"error": "You do not have permission to delete this comment"},
                status=status.HTTP_403_FORBIDDEN,
            )

        with transaction.atomic():
            generation = comment.generation
            is_top_level = comment.parent is None

            comment.delete()

            # Update comment count (only for top-level comments)
            if is_top_level:
                generation.comment_count = max(0, generation.comment_count - 1)
                generation.save(update_fields=["comment_count"])

        return Response(status=status.HTTP_204_NO_CONTENT)


class UserViewSet(viewsets.GenericViewSet):
    """
    ViewSet for user-related actions.

    retrieve: GET /api/users/:id - Get user profile
    update: PATCH /api/users/me - Update own profile
    follow: POST /api/users/:id/follow - Toggle follow
    following: GET /api/users/following - List users current user follows
    """

    serializer_class = UserProfileSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = PageNumberPagination
    queryset = User.objects.all()

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "update":
            return UserUpdateSerializer
        elif self.action == "following":
            return FollowingUserSerializer
        return UserProfileSerializer

    def retrieve(self, request, pk=None):
        """
        Get user profile.

        GET /api/users/:id
        """
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"success": False, "error": {"code": "NOT_FOUND", "message": "User not found"}},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = UserProfileSerializer(user)
        return Response(
            {"success": True, "data": serializer.data}, status=status.HTTP_200_OK
        )

    @action(detail=False, methods=["patch"], permission_classes=[IsAuthenticated])
    def me(self, request):
        """
        Update current user's profile.

        PATCH /api/users/me
        """
        serializer = UserUpdateSerializer(request.user, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            # Return full profile data after update
            profile_serializer = UserProfileSerializer(request.user)
            return Response(
                {"success": True, "data": profile_serializer.data},
                status=status.HTTP_200_OK,
            )

        return Response(
            {
                "success": False,
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Invalid data",
                    "details": serializer.errors,
                },
            },
            status=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )

    @action(detail=False, methods=["post"], url_path="upgrade-to-artist", permission_classes=[IsAuthenticated])
    def upgrade_to_artist(self, request):
        """
        Upgrade current user to artist role.

        POST /api/users/upgrade-to-artist/
        Response: {"success": true, "data": {...}}

        IMPORTANT: User MUST have a signature before upgrading to artist.
        """
        user = request.user

        # Check if already an artist
        if user.role == "artist":
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "ALREADY_ARTIST",
                        "message": "You are already an artist",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # CRITICAL: Validate that user has provided a signature
        try:
            artist_profile = Artist.objects.get(user=user)
            if not artist_profile.signature_image_url:
                return Response(
                    {
                        "success": False,
                        "error": {
                            "code": "SIGNATURE_REQUIRED",
                            "message": "You must provide a signature before upgrading to artist account",
                        },
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Artist.DoesNotExist:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": "SIGNATURE_REQUIRED",
                        "message": "You must provide a signature before upgrading to artist account",
                    },
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Upgrade to artist
        user.role = "artist"
        user.save(update_fields=["role"])

        # Return updated profile
        serializer = UserProfileSerializer(user)
        return Response(
            {
                "success": True,
                "data": serializer.data,
                "message": "Successfully upgraded to artist account",
            },
            status=status.HTTP_200_OK,
        )

    @action(detail=True, methods=["post"])
    def follow(self, request, pk=None):
        """
        Toggle follow on a user.

        POST /api/users/:id/follow
        Response: {"is_following": true/false, "follower_count": int}
        """
        try:
            target_user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        # Cannot follow yourself
        if target_user == request.user:
            return Response(
                {"error": "You cannot follow yourself"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        with transaction.atomic():
            follow_obj = Follow.objects.filter(
                follower=request.user, following=target_user
            ).first()

            if follow_obj:
                # Unfollow
                follow_obj.delete()
                is_following = False
            else:
                # Follow
                Follow.objects.create(follower=request.user, following=target_user)
                is_following = True

            # Get current follower count
            follower_count = Follow.objects.filter(following=target_user).count()

        return Response(
            FollowToggleSerializer(
                {"is_following": is_following, "follower_count": follower_count}
            ).data,
            status=status.HTTP_200_OK,
        )

    @action(detail=False, methods=["get"])
    def following(self, request):
        """
        List users that current user is following.

        GET /api/users/following
        """
        following_ids = Follow.objects.filter(follower=request.user).values_list(
            "following_id", flat=True
        )

        users_queryset = (
            User.objects.filter(id__in=following_ids)
            .prefetch_related("followers")
            .order_by("username")
        )

        page = self.paginate_queryset(users_queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(users_queryset, many=True)
        return Response(serializer.data)
