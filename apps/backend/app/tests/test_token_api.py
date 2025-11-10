"""
Tests for Token System API (M2-Token-API).

Tests:
- GET /api/tokens/balance/ - Get token balance
- POST /api/tokens/purchase/ - Purchase tokens
- GET /api/tokens/transactions/ - List transactions with filtering
- Authentication requirements
- Pagination
"""
from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework import status

from app.models import User, Transaction
from app.services.token_service import TokenService


class TestTokenAPI(TestCase):
    """Test Token API endpoints."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = APIClient()

        # Create test user
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            provider="google",
            provider_user_id="user123",
            token_balance=1000,
        )

        # Create another user
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            provider="google",
            provider_user_id="user456",
            token_balance=500,
        )

        # Create some transactions for user
        TokenService.add_tokens(
            user_id=self.user.id, amount=500, reason="Welcome bonus", transaction_type="earn"
        )
        TokenService.consume_tokens(
            user_id=self.user.id, amount=200, reason="Image generation"
        )
        TokenService.consume_tokens(
            user_id=self.user.id, amount=100, reason="Style training"
        )

    def test_balance_requires_authentication(self):
        """Anonymous users cannot access balance."""
        response = self.client.get("/api/tokens/balance/")
        self.assertIn(
            response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_balance_returns_correct_value(self):
        """Authenticated user can get their balance."""
        # Refresh user to get updated balance
        self.user.refresh_from_db()

        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/tokens/balance/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        # Initial 1000 + 500 (earn) - 200 - 100 (consume) = 1200
        self.assertEqual(response.data["data"]["balance"], 1200)

    def test_purchase_requires_authentication(self):
        """Anonymous users cannot purchase tokens."""
        response = self.client.post("/api/tokens/purchase/", {})
        self.assertIn(
            response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_purchase_tokens_success(self):
        """User can purchase tokens."""
        # Refresh user to get current balance
        self.user.refresh_from_db()
        initial_balance = self.user.token_balance  # Current balance after setUp

        self.client.force_authenticate(user=self.user)

        data = {"amount": 1000, "payment_method": "mock"}

        response = self.client.post("/api/tokens/purchase/", data)

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["data"]["balance"], initial_balance + 1000)
        self.assertIn("transaction", response.data["data"])
        self.assertIn("Successfully purchased", response.data["message"])

        # Verify user balance updated
        self.user.refresh_from_db()
        self.assertEqual(self.user.token_balance, initial_balance + 1000)

        # Verify transaction created
        transaction = Transaction.objects.filter(
            receiver=self.user, transaction_type="purchase"
        ).latest("created_at")
        self.assertEqual(transaction.amount, 1000)
        self.assertEqual(transaction.status, "completed")

    def test_purchase_tokens_validation(self):
        """Test purchase validation rules."""
        self.client.force_authenticate(user=self.user)

        # Test minimum amount (< 100)
        response = self.client.post("/api/tokens/purchase/", {"amount": 50})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test maximum amount (> 1,000,000)
        response = self.client.post("/api/tokens/purchase/", {"amount": 2000000})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

        # Test non-multiple of 100
        response = self.client.post("/api/tokens/purchase/", {"amount": 150})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_transactions_requires_authentication(self):
        """Anonymous users cannot access transactions."""
        response = self.client.get("/api/tokens/transactions/")
        self.assertIn(
            response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
        )

    def test_transactions_list(self):
        """User can list their transactions."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/tokens/transactions/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertIn("results", response.data["data"])

        # Should have 3 transactions (1 earn + 2 consume)
        results = response.data["data"]["results"]
        self.assertEqual(len(results), 3)

        # Verify transaction fields
        transaction = results[0]
        self.assertIn("id", transaction)
        self.assertIn("amount", transaction)
        self.assertIn("transaction_type", transaction)
        self.assertIn("direction", transaction)
        self.assertIn("created_at", transaction)

    def test_transactions_filter_by_type(self):
        """User can filter transactions by type."""
        self.client.force_authenticate(user=self.user)

        # Filter by consume
        response = self.client.get("/api/tokens/transactions/?type=consume")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]["results"]
        self.assertEqual(len(results), 2)  # 2 consume transactions
        for tx in results:
            self.assertEqual(tx["transaction_type"], "consume")

        # Filter by earn
        response = self.client.get("/api/tokens/transactions/?type=earn")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]["results"]
        self.assertEqual(len(results), 1)  # 1 earn transaction
        self.assertEqual(results[0]["transaction_type"], "earn")

    def test_transactions_pagination(self):
        """Test transaction pagination."""
        self.client.force_authenticate(user=self.user)

        # Create more transactions to test pagination
        for i in range(25):
            TokenService.consume_tokens(
                user_id=self.user.id, amount=10, reason=f"Test transaction {i}"
            )

        response = self.client.get("/api/tokens/transactions/?limit=10")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("next", response.data["data"])
        self.assertIn("previous", response.data["data"])
        results = response.data["data"]["results"]
        # Should return 10 results
        self.assertLessEqual(len(results), 10)

    def test_transactions_direction(self):
        """Test transaction direction field."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/tokens/transactions/")
        results = response.data["data"]["results"]

        for tx in results:
            if tx["transaction_type"] == "earn":
                # User received tokens
                self.assertEqual(tx["direction"], "incoming")
            elif tx["transaction_type"] == "consume":
                # User spent tokens
                self.assertEqual(tx["direction"], "outgoing")

    def test_user_only_sees_own_transactions(self):
        """User can only see their own transactions."""
        self.client.force_authenticate(user=self.user2)

        response = self.client.get("/api/tokens/transactions/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        results = response.data["data"]["results"]
        # user2 has no transactions
        self.assertEqual(len(results), 0)

    def test_transactions_ordering(self):
        """Transactions should be ordered by created_at DESC."""
        self.client.force_authenticate(user=self.user)

        # Create transactions at different times
        tx1 = TokenService.consume_tokens(
            user_id=self.user.id, amount=10, reason="First"
        )
        tx2 = TokenService.consume_tokens(
            user_id=self.user.id, amount=20, reason="Second"
        )
        tx3 = TokenService.consume_tokens(
            user_id=self.user.id, amount=30, reason="Third"
        )

        response = self.client.get("/api/tokens/transactions/")
        results = response.data["data"]["results"]

        # Most recent transaction should be first
        # Get transaction IDs from results
        tx_ids = [tx["id"] for tx in results[:3]]

        # Verify that tx3, tx2, tx1 are in the first 3 results (in that order)
        # Since there are also setup transactions, we just verify ordering
        tx1_idx = next((i for i, tx in enumerate(results) if tx["id"] == tx1.id), None)
        tx2_idx = next((i for i, tx in enumerate(results) if tx["id"] == tx2.id), None)
        tx3_idx = next((i for i, tx in enumerate(results) if tx["id"] == tx3.id), None)

        # tx3 should come before tx2, tx2 before tx1
        self.assertIsNotNone(tx1_idx)
        self.assertIsNotNone(tx2_idx)
        self.assertIsNotNone(tx3_idx)
        self.assertLess(tx3_idx, tx2_idx)
        self.assertLess(tx2_idx, tx1_idx)


print("Token API tests created successfully!")
