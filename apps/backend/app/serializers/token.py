"""
Token Serializers for Token System API.

Provides serializers for:
- TokenBalanceSerializer: User's current token balance
- TokenPurchaseSerializer: Token purchase request
- TokenTransactionSerializer: Transaction history
"""
from rest_framework import serializers
from app.models import Transaction, Purchase, User


class TokenBalanceSerializer(serializers.Serializer):
    """
    Serializer for user's token balance.

    Returns only the balance field.
    """

    balance = serializers.IntegerField(read_only=True)


class TokenPurchaseSerializer(serializers.Serializer):
    """
    Serializer for token purchase request.

    For now, this is a mock implementation that always succeeds.
    In production, this would integrate with Toss or other payment gateways.
    """

    amount = serializers.IntegerField(
        min_value=100,
        max_value=1000000,
        help_text="Number of tokens to purchase (100-1,000,000)",
    )
    payment_method = serializers.ChoiceField(
        choices=["mock", "toss", "card"],
        default="mock",
        help_text="Payment method (mock for testing)",
    )

    def validate_amount(self, value):
        """Validate token amount."""
        if value < 100:
            raise serializers.ValidationError("Minimum purchase is 100 tokens")
        if value > 1000000:
            raise serializers.ValidationError("Maximum purchase is 1,000,000 tokens")
        # Only allow multiples of 100
        if value % 100 != 0:
            raise serializers.ValidationError("Amount must be a multiple of 100")
        return value

    def create(self, validated_data):
        """
        Process token purchase.

        For now, this is a mock implementation.
        In production, this would:
        1. Create Purchase record with status='pending'
        2. Call payment gateway API
        3. Wait for webhook callback
        4. Call TokenService.add_tokens() on success
        """
        amount = validated_data["amount"]
        payment_method = validated_data["payment_method"]
        user = self.context["request"].user

        # Mock: Assume payment always succeeds
        from app.services.token_service import TokenService

        # Add tokens to user balance
        transaction = TokenService.add_tokens(
            user_id=user.id,
            amount=amount,
            reason=f"Token purchase via {payment_method}",
            transaction_type="purchase",
        )

        # Return new balance and transaction
        return {"balance": user.token_balance + amount, "transaction": transaction}


class TokenTransactionSerializer(serializers.ModelSerializer):
    """
    Serializer for Token Transaction history.

    Shows all fields needed for transaction display:
    - id, amount, type, status
    - sender/receiver usernames
    - related objects (style, generation)
    - timestamps
    """

    sender_username = serializers.CharField(
        source="sender.username", read_only=True, allow_null=True
    )
    receiver_username = serializers.CharField(
        source="receiver.username", read_only=True, allow_null=True
    )

    # Related object names
    related_style_name = serializers.CharField(
        source="related_style.name", read_only=True, allow_null=True
    )
    related_generation_id = serializers.IntegerField(
        source="related_generation.id", read_only=True, allow_null=True
    )

    # Computed field
    total_price = serializers.SerializerMethodField()

    # Transaction direction (incoming/outgoing)
    direction = serializers.SerializerMethodField()

    class Meta:
        model = Transaction
        fields = [
            "id",
            "amount",
            "transaction_type",
            "status",
            "direction",
            "sender_username",
            "receiver_username",
            "related_style_name",
            "related_generation_id",
            "price_per_token",
            "currency_code",
            "total_price",
            "payment_method",
            "refunded",
            "memo",
            "created_at",
        ]
        read_only_fields = fields

    def get_total_price(self, obj):
        """Calculate total price if price_per_token is set."""
        return obj.total_price

    def get_direction(self, obj):
        """
        Determine transaction direction for current user.

        Returns:
        - 'incoming': User received tokens (receiver)
        - 'outgoing': User spent tokens (sender)
        - 'system': System transaction (neither sender nor receiver is user)
        """
        request = self.context.get("request")
        if not request or not request.user.is_authenticated:
            return None

        user = request.user

        if obj.receiver_id == user.id:
            return "incoming"
        elif obj.sender_id == user.id:
            return "outgoing"
        else:
            return "system"
