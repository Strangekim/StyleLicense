"""
Tests for Token Transaction Atomicity (M2-Token-Service).

Tests:
- Concurrent token consumption without race conditions
- Token balance accuracy after concurrent operations
- All transactions logged correctly
- SELECT FOR UPDATE prevents lost updates
"""
import threading
from django.test import TestCase, TransactionTestCase
from django.db import connection
from django.db.models import Sum

from app.models import User, Transaction
from app.services.token_service import TokenService


class TestTokenConcurrency(TransactionTestCase):
    """
    Test token service concurrency with real database transactions.

    Note: Uses TransactionTestCase instead of TestCase to properly test
    database-level transaction isolation and SELECT FOR UPDATE.
    """

    def setUp(self):
        """Set up test user with initial balance."""
        self.user = User.objects.create_user(
            username="concurrency_test_user",
            provider="google",
            provider_user_id="concurrent123",
            email="concurrent@example.com",
            token_balance=10000  # Start with 10,000 tokens
        )
        self.initial_balance = 10000

    def test_concurrent_consume_tokens_no_race_condition(self):
        """
        Test that 20 concurrent consume_tokens calls don't cause race conditions.

        This test verifies that SELECT FOR UPDATE properly serializes concurrent
        token consumptions, preventing lost updates.
        """
        num_threads = 20
        tokens_per_thread = 10
        expected_final_balance = self.initial_balance - (num_threads * tokens_per_thread)

        errors = []
        success_count = [0]  # Use list to allow mutation in thread
        lock = threading.Lock()

        def consume_tokens_thread():
            """Thread function to consume tokens."""
            try:
                # Each thread consumes 10 tokens
                TokenService.consume_tokens(
                    user_id=self.user.id,
                    amount=tokens_per_thread,
                    reason=f"Concurrent test - Thread {threading.current_thread().name}"
                )
                with lock:
                    success_count[0] += 1
            except Exception as e:
                with lock:
                    errors.append(str(e))

        # Create and start 100 threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=consume_tokens_thread, name=f"Thread-{i}")
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")
        self.assertEqual(success_count[0], num_threads, "Not all threads succeeded")

        # Refresh user from database
        self.user.refresh_from_db()

        # Verify final balance is correct (no lost updates)
        self.assertEqual(
            self.user.token_balance,
            expected_final_balance,
            f"Race condition detected! Expected {expected_final_balance}, got {self.user.token_balance}"
        )

        # Verify all transactions were logged
        transaction_count = Transaction.objects.filter(
            sender_id=self.user.id,
            transaction_type="consume"
        ).count()
        self.assertEqual(transaction_count, num_threads, "Not all transactions were logged")

        # Verify total consumed amount matches
        expected_total = num_threads * tokens_per_thread
        transactions = Transaction.objects.filter(
            sender_id=self.user.id,
            transaction_type="consume"
        )
        total_consumed = sum(t.amount for t in transactions)

        self.assertEqual(total_consumed, expected_total)

    def test_concurrent_add_and_consume_tokens(self):
        """
        Test concurrent add_tokens and consume_tokens operations.

        This ensures both types of operations can happen concurrently
        without causing inconsistencies.
        """
        num_add_threads = 10
        num_consume_threads = 10
        add_amount = 20
        consume_amount = 10

        errors = []
        lock = threading.Lock()

        def add_tokens_thread():
            try:
                TokenService.add_tokens(
                    user_id=self.user.id,
                    amount=add_amount,
                    reason="Concurrent add test"
                )
            except Exception as e:
                with lock:
                    errors.append(f"Add error: {str(e)}")

        def consume_tokens_thread():
            try:
                TokenService.consume_tokens(
                    user_id=self.user.id,
                    amount=consume_amount,
                    reason="Concurrent consume test"
                )
            except Exception as e:
                # Insufficient balance is expected and ok
                if "Insufficient token balance" not in str(e):
                    with lock:
                        errors.append(f"Consume error: {str(e)}")

        # Create threads
        threads = []

        # Add threads
        for i in range(num_add_threads):
            thread = threading.Thread(target=add_tokens_thread, name=f"Add-{i}")
            threads.append(thread)

        # Consume threads
        for i in range(num_consume_threads):
            thread = threading.Thread(target=consume_tokens_thread, name=f"Consume-{i}")
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify no unexpected errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

        # Refresh user
        self.user.refresh_from_db()

        # Calculate expected balance
        add_transactions = Transaction.objects.filter(
            receiver_id=self.user.id
        ).exclude(transaction_type="consume")
        consume_transactions = Transaction.objects.filter(
            sender_id=self.user.id,
            transaction_type="consume"
        )

        total_added = sum(t.amount for t in add_transactions)
        total_consumed = sum(t.amount for t in consume_transactions)
        expected_balance = self.initial_balance + total_added - total_consumed

        # Verify balance matches
        self.assertEqual(
            self.user.token_balance,
            expected_balance,
            f"Balance mismatch! Expected {expected_balance}, got {self.user.token_balance}"
        )

    def test_insufficient_balance_during_concurrent_consumption(self):
        """
        Test that insufficient balance errors are raised correctly
        when multiple threads try to consume more than available balance.
        """
        # Set low balance
        self.user.token_balance = 100
        self.user.save()

        num_threads = 10
        tokens_per_thread = 50  # Total would be 500, but only 100 available

        successful_consumptions = [0]
        insufficient_balance_errors = [0]
        lock = threading.Lock()

        def consume_tokens_thread():
            try:
                TokenService.consume_tokens(
                    user_id=self.user.id,
                    amount=tokens_per_thread,
                    reason="Insufficient balance test"
                )
                with lock:
                    successful_consumptions[0] += 1
            except ValueError as e:
                if "Insufficient token balance" in str(e):
                    with lock:
                        insufficient_balance_errors[0] += 1

        # Create and start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=consume_tokens_thread)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Only 2 threads should succeed (2 * 50 = 100)
        # The rest should get insufficient balance errors
        self.assertEqual(successful_consumptions[0], 2, "Expected exactly 2 successful consumptions")
        self.assertEqual(insufficient_balance_errors[0], 8, "Expected 8 insufficient balance errors")

        # Verify final balance is 0
        self.user.refresh_from_db()
        self.assertEqual(self.user.token_balance, 0)

    def test_refund_tokens_concurrency(self):
        """Test that concurrent refunds work correctly."""
        num_threads = 20
        refund_amount = 10

        errors = []
        lock = threading.Lock()

        def refund_tokens_thread():
            try:
                TokenService.refund_tokens(
                    user_id=self.user.id,
                    amount=refund_amount,
                    reason="Concurrent refund test"
                )
            except Exception as e:
                with lock:
                    errors.append(str(e))

        # Create and start threads
        threads = []
        for i in range(num_threads):
            thread = threading.Thread(target=refund_tokens_thread)
            threads.append(thread)
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Verify no errors
        self.assertEqual(len(errors), 0, f"Errors occurred: {errors}")

        # Verify balance increased correctly
        expected_balance = self.initial_balance + (num_threads * refund_amount)
        self.user.refresh_from_db()
        self.assertEqual(self.user.token_balance, expected_balance)


print("Token concurrency tests created successfully!")
