"""
Token Service for managing user token balance and transactions.
"""
from django.db import transaction
from app.models import User, Transaction


class TokenService:
    """Service for token operations with atomicity guaranteed."""

    @staticmethod
    @transaction.atomic
    def add_tokens(
        user_id: int, amount: int, reason: str, transaction_type: str = "purchase"
    ):
        """
        Add tokens to user balance atomically.

        Args:
            user_id: User ID to add tokens to
            amount: Amount of tokens to add (must be positive)
            reason: Reason for adding tokens (e.g., 'welcome_bonus', 'purchase')
            transaction_type: Type of transaction ('purchase' or 'transfer')

        Returns:
            Transaction: Created transaction record

        Raises:
            ValueError: If amount is not positive
            User.DoesNotExist: If user not found
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Lock user row for update
        user = User.objects.select_for_update().get(id=user_id)

        # Update balance
        user.token_balance += amount
        user.save(update_fields=["token_balance", "updated_at"])

        # Create transaction record
        trans = Transaction.objects.create(
            receiver=user,
            amount=amount,
            transaction_type=transaction_type,
            status="completed",
            memo=reason,
        )

        return trans

    @staticmethod
    @transaction.atomic
    def consume_tokens(
        user_id: int,
        amount: int,
        reason: str,
        related_generation_id=None,
        related_style_id=None,
    ):
        """
        Consume tokens from user balance atomically.

        Args:
            user_id: User ID to consume tokens from
            amount: Amount of tokens to consume (must be positive)
            reason: Reason for consuming tokens
            related_generation_id: Optional generation ID (for image generation)
            related_style_id: Optional style ID (for style usage)

        Returns:
            Transaction: Created transaction record

        Raises:
            ValueError: If amount is not positive or insufficient balance
            User.DoesNotExist: If user not found
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Lock user row for update
        user = User.objects.select_for_update().get(id=user_id)

        # Check sufficient balance
        if user.token_balance < amount:
            raise ValueError(
                f"Insufficient token balance. Required: {amount}, Available: {user.token_balance}"
            )

        # Update balance
        user.token_balance -= amount
        user.save(update_fields=["token_balance", "updated_at"])

        # Create transaction record
        trans = Transaction.objects.create(
            sender=user,
            amount=amount,
            transaction_type="consume",
            status="completed",
            memo=reason,
            related_generation_id=related_generation_id,
            related_style_id=related_style_id,
        )

        return trans

    @staticmethod
    @transaction.atomic
    def refund_tokens(
        user_id: int, amount: int, reason: str, related_generation_id=None
    ):
        """
        Refund tokens to user balance atomically.

        Args:
            user_id: User ID to refund tokens to
            amount: Amount of tokens to refund (must be positive)
            reason: Reason for refund (e.g., 'generation_failed')
            related_generation_id: Optional generation ID

        Returns:
            Transaction: Created transaction record

        Raises:
            ValueError: If amount is not positive
            User.DoesNotExist: If user not found
        """
        if amount <= 0:
            raise ValueError("Amount must be positive")

        # Lock user row for update
        user = User.objects.select_for_update().get(id=user_id)

        # Update balance
        user.token_balance += amount
        user.save(update_fields=["token_balance", "updated_at"])

        # Create transaction record (marked as refund)
        trans = Transaction.objects.create(
            receiver=user,
            amount=amount,
            transaction_type="generation",
            status="completed",
            memo=reason,
            related_generation_id=related_generation_id,
            refunded=True,
        )

        return trans

    @staticmethod
    def get_balance(user_id: int) -> int:
        """
        Get user's current token balance.

        Args:
            user_id: User ID

        Returns:
            int: Current token balance

        Raises:
            User.DoesNotExist: If user not found
        """
        user = User.objects.get(id=user_id)
        return user.token_balance
