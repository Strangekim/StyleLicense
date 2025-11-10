"""
Token ViewSet for Token System API.

Endpoints:
- GET /api/tokens/balance/ - Get current user's token balance
- POST /api/tokens/purchase/ - Purchase tokens (mock payment)
- GET /api/tokens/transactions/ - List transaction history
"""
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from app.models import Transaction
from app.serializers import (
    TokenBalanceSerializer,
    TokenPurchaseSerializer,
    TokenTransactionSerializer,
)
from app.views.base import CustomCursorPagination


class TokenViewSet(viewsets.GenericViewSet):
    """
    ViewSet for Token operations.

    This is a custom ViewSet (not ModelViewSet) because token operations
    are service-based, not CRUD-based.

    Permissions:
    - All actions require authentication

    Actions:
    - balance: GET /api/tokens/balance/
    - purchase: POST /api/tokens/purchase/
    - transactions: GET /api/tokens/transactions/
    """

    permission_classes = [IsAuthenticated]
    pagination_class = CustomCursorPagination

    @action(detail=False, methods=["get"], url_path="balance")
    def balance(self, request):
        """
        Get current user's token balance.

        Returns:
        {
            "success": true,
            "data": {
                "balance": 1000
            }
        }
        """
        user = request.user
        serializer = TokenBalanceSerializer({"balance": user.token_balance})
        return Response({"success": True, "data": serializer.data})

    @action(detail=False, methods=["post"], url_path="purchase")
    def purchase(self, request):
        """
        Purchase tokens.

        Request body:
        {
            "amount": 1000,
            "payment_method": "mock"
        }

        Response:
        {
            "success": true,
            "data": {
                "balance": 2000,
                "transaction": {...}
            },
            "message": "Successfully purchased 1000 tokens"
        }

        For now, this is a mock implementation that always succeeds.
        In production, this would integrate with payment gateways.
        """
        serializer = TokenPurchaseSerializer(
            data=request.data, context={"request": request}
        )
        serializer.is_valid(raise_exception=True)

        # Process purchase (mock)
        result = serializer.save()

        # Refresh user to get updated balance
        request.user.refresh_from_db()

        return Response(
            {
                "success": True,
                "data": {
                    "balance": request.user.token_balance,
                    "transaction": TokenTransactionSerializer(
                        result["transaction"], context={"request": request}
                    ).data,
                },
                "message": f"Successfully purchased {serializer.validated_data['amount']} tokens",
            },
            status=status.HTTP_201_CREATED,
        )

    @action(detail=False, methods=["get"], url_path="transactions")
    def transactions(self, request):
        """
        List user's transaction history.

        Query parameters:
        - ?type=consume - Filter by transaction type
        - ?type=purchase - Filter by transaction type
        - ?cursor=<encoded> - For pagination
        - ?limit=20 - Page size

        Returns paginated list of transactions.
        """
        user = request.user

        # Get all transactions where user is either sender or receiver
        queryset = Transaction.objects.filter(
            Q(sender=user) | Q(receiver=user)
        ).select_related("sender", "receiver", "related_style", "related_generation")

        # Filter by transaction type
        transaction_type = request.query_params.get("type")
        if transaction_type and transaction_type in [
            "purchase",
            "earn",
            "consume",
            "generation",
            "withdrawal",
            "transfer",
        ]:
            queryset = queryset.filter(transaction_type=transaction_type)

        # Order by created_at DESC (most recent first)
        queryset = queryset.order_by("-created_at")

        # Paginate
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = TokenTransactionSerializer(
                page, many=True, context={"request": request}
            )
            return self.get_paginated_response(serializer.data)

        # No pagination (shouldn't happen with pagination_class set)
        serializer = TokenTransactionSerializer(
            queryset, many=True, context={"request": request}
        )
        return Response({"success": True, "data": serializer.data})

    def get_paginated_response(self, data):
        """
        Override to wrap paginated response with success/data structure.
        """
        paginator = self.paginator
        return Response(
            {
                "success": True,
                "data": {
                    "next": paginator.get_next_link(),
                    "previous": paginator.get_previous_link(),
                    "results": data,
                },
            }
        )
