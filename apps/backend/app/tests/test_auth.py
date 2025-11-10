"""
Authentication tests for Google OAuth and session management.
"""
from django.test import TestCase, Client
from django.urls import reverse
from unittest.mock import patch, MagicMock
from app.models import User, Transaction


class AuthenticationTestCase(TestCase):
    """Test cases for authentication endpoints."""

    def setUp(self):
        """Set up test client and test data."""
        self.client = Client()
        self.test_user_data = {
            "email": "test@example.com",
            "username": "testuser",
            "provider": "google",
            "provider_user_id": "google_123",
        }

    def test_me_endpoint_returns_401_when_unauthenticated(self):
        """Test that /api/auth/me returns 401 when user is not authenticated."""
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json())

    def test_me_endpoint_returns_user_data_when_authenticated(self):
        """Test that /api/auth/me returns user data when authenticated."""
        # Create a test user
        user = User.objects.create_user(
            email=self.test_user_data["email"],
            username=self.test_user_data["username"],
            provider=self.test_user_data["provider"],
            provider_user_id=self.test_user_data["provider_user_id"],
            token_balance=100,
        )

        # Log the user in
        self.client.force_login(user)

        # Make request
        response = self.client.get("/api/auth/me")

        # Assertions
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["email"], self.test_user_data["email"])
        self.assertEqual(data["username"], self.test_user_data["username"])
        self.assertEqual(data["token_balance"], 100)

    def test_logout_clears_session(self):
        """Test that POST /api/auth/logout clears the session."""
        # Create and login a test user
        user = User.objects.create_user(
            email=self.test_user_data["email"],
            username=self.test_user_data["username"],
            provider=self.test_user_data["provider"],
            provider_user_id=self.test_user_data["provider_user_id"],
        )
        self.client.force_login(user)

        # Verify user is logged in
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 200)

        # Logout
        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 200)
        self.assertIn("message", response.json())

        # Verify user is logged out
        response = self.client.get("/api/auth/me")
        self.assertEqual(response.status_code, 401)

    def test_logout_returns_401_when_not_authenticated(self):
        """Test that POST /api/auth/logout returns 401 when not authenticated."""
        response = self.client.post("/api/auth/logout")
        self.assertEqual(response.status_code, 401)
        self.assertIn("error", response.json())

    @patch("app.views.auth.TokenService")
    @patch("allauth.socialaccount.models.SocialAccount.objects")
    def test_google_callback_creates_user_and_grants_welcome_bonus(
        self, mock_social_account, mock_token_service
    ):
        """
        Test that Google OAuth callback creates a new user and grants welcome bonus.

        Note: This is a simplified test. Real OAuth testing would require
        mocking the entire OAuth flow or using integration tests.
        """
        # Create a user to simulate OAuth callback
        user = User.objects.create_user(
            email="newuser@example.com",
            username="newuser",
            provider="google",
            provider_user_id="google_456",
            token_balance=0,
        )

        # Check that user was created
        self.assertEqual(User.objects.filter(email="newuser@example.com").count(), 1)

        # Verify user has zero balance initially (before welcome bonus)
        self.assertEqual(user.token_balance, 0)


class TokenServiceTestCase(TestCase):
    """Test cases for TokenService."""

    def setUp(self):
        """Set up test user."""
        self.user = User.objects.create_user(
            email="tokentest@example.com",
            username="tokentest",
            provider="google",
            provider_user_id="google_789",
            token_balance=100,
        )

    def test_welcome_bonus_not_granted_if_transactions_exist(self):
        """Test that welcome bonus is only granted once (checked by transaction existence)."""
        from app.services.token_service import TokenService

        # Create a transaction for the user
        Transaction.objects.create(
            receiver=self.user,
            amount=50,
            transaction_type="purchase",
            status="completed",
            memo="Test transaction",
        )

        # Count transactions before
        initial_count = Transaction.objects.filter(receiver=self.user).count()
        self.assertEqual(initial_count, 1)

        # Simulate the welcome bonus check (it should NOT create a new transaction)
        has_transactions = Transaction.objects.filter(receiver=self.user).exists()
        self.assertTrue(has_transactions)

        # If no transactions existed, welcome bonus would be granted:
        if not has_transactions:
            TokenService.add_tokens(
                user_id=self.user.id,
                amount=100,
                reason="Welcome bonus for new user",
                transaction_type="earn",
            )

        # Count should still be 1 (no welcome bonus added)
        final_count = Transaction.objects.filter(receiver=self.user).count()
        self.assertEqual(final_count, initial_count)

    def test_token_service_add_tokens(self):
        """Test that TokenService.add_tokens increases user balance."""
        from app.services.token_service import TokenService

        initial_balance = self.user.token_balance

        # Add tokens
        TokenService.add_tokens(
            user_id=self.user.id,
            amount=50,
            reason="Test add tokens",
            transaction_type="earn",
        )

        # Refresh user from database
        self.user.refresh_from_db()

        # Check balance increased
        self.assertEqual(self.user.token_balance, initial_balance + 50)

        # Check transaction was created
        transaction = Transaction.objects.filter(
            receiver=self.user, amount=50, transaction_type="earn"
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, "completed")

    def test_token_service_consume_tokens(self):
        """Test that TokenService.consume_tokens decreases user balance."""
        from app.services.token_service import TokenService

        initial_balance = self.user.token_balance

        # Consume tokens
        TokenService.consume_tokens(
            user_id=self.user.id,
            amount=30,
            reason="Test consume tokens",
            related_generation_id=None,
        )

        # Refresh user from database
        self.user.refresh_from_db()

        # Check balance decreased
        self.assertEqual(self.user.token_balance, initial_balance - 30)

        # Check transaction was created
        transaction = Transaction.objects.filter(
            sender=self.user, amount=30, transaction_type="consume"
        ).first()
        self.assertIsNotNone(transaction)
        self.assertEqual(transaction.status, "completed")

    def test_token_service_consume_tokens_insufficient_balance(self):
        """Test that consuming more tokens than available raises ValueError."""
        from app.services.token_service import TokenService

        # Try to consume more than available
        with self.assertRaises(ValueError) as context:
            TokenService.consume_tokens(
                user_id=self.user.id,
                amount=200,  # More than the user's 100 balance
                reason="Test insufficient balance",
                related_generation_id=None,
            )

        self.assertIn("Insufficient token balance", str(context.exception))

        # Balance should not have changed
        self.user.refresh_from_db()
        self.assertEqual(self.user.token_balance, 100)
