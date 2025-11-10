from django.db import models
from django.utils import timezone


class Transaction(models.Model):
    """Token transaction model for all token movements."""

    TRANSACTION_TYPE_CHOICES = [
        ("purchase", "Purchase"),
        ("earn", "Earn"),
        ("consume", "Consume"),
        ("generation", "Generation"),
        ("withdrawal", "Withdrawal"),
        ("transfer", "Transfer"),
    ]

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Foreign keys
    sender = models.ForeignKey(
        "app.User",
        on_delete=models.CASCADE,
        related_name="sent_transactions",
        null=True,
        blank=True,
    )
    receiver = models.ForeignKey(
        "app.User",
        on_delete=models.CASCADE,
        related_name="received_transactions",
        null=True,
        blank=True,
    )

    # Transaction details
    amount = models.BigIntegerField()
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPE_CHOICES)
    price_per_token = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    currency_code = models.CharField(max_length=3, default="KRW")
    # total_price is computed (amount * price_per_token), not stored in Django

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="completed"
    )
    memo = models.TextField(null=True, blank=True)

    # Related objects
    related_style = models.ForeignKey(
        "app.Style",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )
    related_generation = models.ForeignKey(
        "app.Generation",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="transactions",
    )

    # Payment details
    payment_method = models.CharField(max_length=30, default="token")
    refunded = models.BooleanField(default=False)

    # Timestamp
    created_at = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "transactions"
        constraints = [
            models.CheckConstraint(
                check=models.Q(
                    transaction_type__in=[
                        "purchase",
                        "earn",
                        "consume",
                        "generation",
                        "withdrawal",
                        "transfer",
                    ]
                ),
                name="valid_transaction_type",
            ),
            models.CheckConstraint(
                check=models.Q(status__in=["pending", "completed", "failed"]),
                name="valid_transaction_status",
            ),
        ]
        indexes = [
            models.Index(
                fields=["sender", "-created_at"], name="idx_transactions_sender"
            ),
            models.Index(
                fields=["receiver", "-created_at"], name="idx_transactions_receiver"
            ),
            models.Index(
                fields=["transaction_type", "-created_at"], name="idx_transactions_type"
            ),
            models.Index(fields=["related_style"], name="idx_transactions_style"),
            models.Index(
                fields=["related_generation"], name="idx_transactions_generation"
            ),
            models.Index(
                fields=["status", "-created_at"], name="idx_transactions_status"
            ),
        ]

    def __str__(self):
        return f"{self.transaction_type} - {self.amount} tokens ({self.status})"

    @property
    def total_price(self):
        """Computed property for total price."""
        if self.price_per_token and self.amount:
            return self.amount * self.price_per_token
        return None


class Purchase(models.Model):
    """Token purchase model for Toss payment integration."""

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("authorized", "Authorized"),
        ("paid", "Paid"),
        ("failed", "Failed"),
    ]

    PROVIDER_CHOICES = [
        ("toss", "Toss"),
    ]

    # Primary key
    id = models.BigAutoField(primary_key=True)

    # Foreign key
    buyer = models.ForeignKey(
        "app.User", on_delete=models.CASCADE, related_name="purchases"
    )

    # Purchase details
    amount_tokens = models.BigIntegerField()
    price_per_token = models.DecimalField(max_digits=18, decimal_places=4)
    currency_code = models.CharField(max_length=3, default="KRW")
    # total_price is computed (amount_tokens * price_per_token), not stored in Django

    # Provider details
    provider = models.CharField(max_length=30, choices=PROVIDER_CHOICES, default="toss")
    provider_payment_key = models.CharField(max_length=120, unique=True)
    provider_order_id = models.CharField(max_length=120)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Payment timestamps
    approved_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    # Toss-specific details (JSONB in PostgreSQL)
    provider_total_amount = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True
    )
    receipt_url = models.TextField(null=True, blank=True)
    card_detail = models.JSONField(null=True, blank=True)
    easy_pay_detail = models.JSONField(null=True, blank=True)
    memo = models.TextField(null=True, blank=True)

    class Meta:
        db_table = "purchases"
        constraints = [
            models.CheckConstraint(
                check=models.Q(amount_tokens__gt=0), name="amount_tokens_positive"
            ),
            models.CheckConstraint(
                check=models.Q(status__in=["pending", "authorized", "paid", "failed"]),
                name="valid_purchase_status",
            ),
        ]
        indexes = [
            models.Index(fields=["buyer", "-created_at"], name="idx_purchases_buyer"),
            models.Index(fields=["status"], name="idx_purchases_status"),
            models.Index(fields=["provider_order_id"], name="idx_purchases_order_id"),
        ]

    def __str__(self):
        return f"Purchase {self.id} - {self.amount_tokens} tokens ({self.status})"

    @property
    def total_price(self):
        """Computed property for total price."""
        return self.amount_tokens * self.price_per_token

    def save(self, *args, **kwargs):
        """Override save to ensure updated_at is set."""
        if not self.id:
            self.created_at = timezone.now()
        self.updated_at = timezone.now()
        super().save(*args, **kwargs)
