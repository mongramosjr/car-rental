from django.test import TestCase
from django.conf import settings
from unittest.mock import patch, MagicMock, Mock
import json
from decimal import Decimal
import stripe
from django.contrib.auth import get_user_model
from payment.services import StripeService
from overdrive.models import Booking
from payment.models import BookingPayment
from payment.stripe_payment import StripeBookingPayment
from fleet_management.models import Car, Owner, Manufacturer
from django.utils import timezone

User = get_user_model()


class StripeServiceTestCase(TestCase):

    def setUp(self):
        self.user = User.objects.create_user(email='testuser@payment.com', password='12345')
        self.user.is_active = True
        self.user.save()
        self.car_owner = User.objects.create_user(email='testcarowner@payment.com', password='12345')
        self.car_owner.is_active = True
        self.car_owner.save()
        self.owner = Owner.objects.create(name="Test Owner", user=self.car_owner)
        self.manufacturer = Manufacturer.objects.create(name="Test Make", country="Test Country")
        self.car = Car.objects.create(
            owner=self.owner,
            license_plate="ABC123",
            passenger_capacity=5,
            make=self.manufacturer,
            model="Test Model", 
            year=2020, 
            price_per_hour=10)
        self.booking = Booking.objects.create(
            user=self.user,
            car=self.car,
            start_time="2023-10-01T12:00:00Z",
            end_time="2023-10-02T12:00:00Z",
            total_price=240,
            status='confirmed'
        )
        self.payment = StripeBookingPayment.objects.create(
            booking=self.booking,
            amount=100.00,
            method='stripe',
            status='pending',
            transaction_id='pi_test_123',
        )
        self.stripe_service = StripeService()

    @patch('payment.services.stripe_service.stripe.PaymentIntent.create')
    def test_process_payment_success(self, mock_create):
        # Mock successful PaymentIntent creation
        mock_intent = {
            'id': 'pi_test_123',
            'status': 'requires_payment_method',
            'client_secret': 'cs_test_456',
            'capture_method': 'automatic',
            'confirmation_method': 'automatic'
        }
        mock_create.return_value = mock_intent

        # Initialize service and execute
        service = StripeService()
        result = service.process_payment(self.payment)

        # Assertions
        self.assertTrue(result)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.transaction_id, 'pi_test_123')
        self.assertEqual(self.payment.status, 'requires_payment_method')
        self.assertEqual(self.payment.client_secret, 'cs_test_456')
        self.assertEqual(self.payment.capture_method, 'automatic')
        self.assertEqual(self.payment.confirmation_method, 'automatic')
        mock_create.assert_called_once_with(
            amount=10000,  # 100.00 * 100 cents
            currency="usd",
            description="Car rental payment",
            automatic_payment_methods={"enabled": True}
        )

    @patch('payment.services.stripe_service.stripe.PaymentIntent.create')
    def test_process_payment_failure(self, mock_create):
        # Mock Stripe error
        mock_create.side_effect = stripe.error.StripeError("Invalid card")

        # Initialize service and execute
        service = StripeService()
        result = service.process_payment(self.payment)

        # Assertions
        self.assertFalse(result)
        self.payment.refresh_from_db()
        self.assertIsNone(self.payment.client_secret)  # Should not update on failure

    @patch('payment.services.stripe_service.stripe.PaymentIntent.confirm')
    def test_confirm_payment_intent_success(self, mock_confirm):
        # Mock successful confirmation
        mock_intent = {'id': 'pi_test_123', 'status': 'requires_confirmation'}
        mock_confirm.return_value = mock_intent

        # Initialize service and execute
        service = StripeService()
        result = service.confirm_payment_intent(self.payment)

        # Assertions
        self.assertTrue(result)
        mock_confirm.assert_called_once_with(
            'pi_test_123',
            payment_method="pm_card_visa"  # Note: Fixed closing quote
        )

    @patch('payment.services.stripe_service.stripe.PaymentIntent.confirm')
    def test_confirm_payment_intent_failure(self, mock_confirm):
        # Mock Stripe error
        mock_confirm.side_effect = stripe.error.StripeError("Payment method error")

        # Initialize service and execute
        service = StripeService()
        result = service.confirm_payment_intent(self.payment)

        # Assertions
        self.assertFalse(result)
        mock_confirm.assert_called_once()

    @patch('payment.services.stripe_service.stripe.PaymentIntent.capture')
    def test_capture_payment_intent_success(self, mock_capture):
        # Mock successful capture
        mock_intent = {'id': 'pi_test_123', 'status': 'succeeded'}
        mock_capture.return_value = mock_intent

        # Initialize service and execute
        service = StripeService()
        result = service.capture_payment_intent(self.payment)

        # Assertions
        self.assertTrue(result)
        mock_capture.assert_called_once_with(
            'pi_test_123',
            payment_method="pm_card_visa"  # Note: Fixed closing quote
        )

    @patch('payment.services.stripe_service.stripe.PaymentIntent.capture')
    def test_capture_payment_intent_failure(self, mock_capture):
        # Mock Stripe error
        mock_capture.side_effect = stripe.error.StripeError("Capture failed")

        # Initialize service and execute
        service = StripeService()
        result = service.capture_payment_intent(self.payment)

        # Assertions
        self.assertFalse(result)
        mock_capture.assert_called_once()
