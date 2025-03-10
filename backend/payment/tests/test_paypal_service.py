from django.test import TestCase
from django.conf import settings
from unittest.mock import patch, MagicMock, Mock
import json
from decimal import Decimal
from django.contrib.auth import get_user_model
from payment.services import PaypalService
from overdrive.models import Booking
from payment.models import BookingPayment
from payment.paypal_payment import PayPalBookingPayment
from fleet_management.models import Car, Owner, Manufacturer, Vehicle
from django.utils import timezone

User = get_user_model()


class PaypalServiceTestCase(TestCase):

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
        # Access Car fields from Vehicle
        self.vehicle = Vehicle.objects.get(id=self.car.id)
        self.booking = Booking.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            start_time="2023-10-01T12:00:00Z",
            end_time="2023-10-02T12:00:00Z",
            total_price=240,
            status='confirmed'
        )
        self.payment = PayPalBookingPayment.objects.create(
            booking=self.booking,
            method='paypal',
            status='pending',
            amount=Decimal('100.00'),
            paypal_request_id='test-request-id-123',
            order_id='test-order-id-456',
            created_at=timezone.now()
        )
        self.paypal_service = PaypalService()

    @patch('payment.services.paypal_service.requests.post')
    def test_get_access_token_success(self, mock_post):
        # Mock successful token response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'access_token': 'test_access_token',
            'token_type': 'Bearer',
            'scope': 'test_scope',
            'app_id': 'test_app_id',
            'expires_in': 3600,
            'nonce': 'test_nonce'
        }
        mock_post.return_value = mock_response

        # Initialize service
        service = PaypalService()

        # Assertions
        self.assertEqual(service.access_token, 'test_access_token')
        self.assertEqual(service.token_type, 'Bearer')
        self.assertEqual(service.scope, 'test_scope')
        self.assertEqual(service.app_id, 'test_app_id')
        self.assertEqual(service.expires_in, 3600)
        self.assertEqual(service.nonce, 'test_nonce')

    @patch('payment.services.paypal_service.requests.post')
    def test_get_access_token_failure(self, mock_post):
        # Mock failed token response
        mock_response = Mock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = Exception("Bad Request")
        mock_post.return_value = mock_response

        # Test exception handling
        with self.assertRaises(Exception) as context:
            PaypalService()
        self.assertIn("Bad Request", str(context.exception))

    @patch('payment.services.paypal_service.requests.post')
    def test_checkout_orders_success(self, mock_post):
        # Mock token response
        with patch.object(PaypalService, '_get_access_token', return_value='test_access_token'):
            service = PaypalService()

            # Mock checkout response
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                'id': 'test-order-id-456',
                'status': 'CREATED'
            }
            mock_post.return_value = mock_response

            # Execute
            order_id = service.checkout_orders(self.payment)

            # Assertions
            self.assertEqual(order_id, 'test-order-id-456')
            self.assertEqual(self.payment.transaction_id, 'test-order-id-456')
            mock_post.assert_called_once()

    @patch('payment.services.paypal_service.requests.post')
    def test_checkout_orders_failure(self, mock_post):
        # Mock token response
        with patch.object(PaypalService, '_get_access_token', return_value='test_access_token'):
            service = PaypalService()

            # Mock failed checkout response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.text = "Invalid request"
            mock_post.return_value = mock_response

            # Execute
            order_id = service.checkout_orders(self.payment)

            # Assertions
            self.assertIsNone(order_id)
            self.assertIsNone(self.payment.transaction_id)

    @patch('payment.services.paypal_service.requests.post')
    def test_confirm_order(self, mock_post):
        # Mock token response
        with patch.object(PaypalService, '_get_access_token', return_value='test_access_token'):
            service = PaypalService()

            # Mock confirm response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_post.return_value = mock_response

            # Execute
            result = service.confirm_order(self.payment)

            # Assertions
            self.assertTrue(result)
            mock_post.assert_called_once()

    @patch('payment.services.paypal_service.requests.post')
    def test_process_payment_success(self, mock_post):
        # Mock token response
        with patch.object(PaypalService, '_get_access_token', return_value='test_access_token'):
            service = PaypalService()

            # Mock capture response
            mock_response = Mock()
            mock_response.status_code = 201
            mock_response.json.return_value = {
                'status': 'COMPLETED',
                'id': 'test-capture-id'
            }
            mock_post.return_value = mock_response

            # Execute
            success, capture_data = service.process_payment(self.payment)

            # Assertions
            self.assertTrue(success)
            self.assertEqual(capture_data['status'], 'COMPLETED')
            mock_post.assert_called_once()

    @patch('payment.services.paypal_service.requests.post')
    def test_process_payment_failure(self, mock_post):
        # Mock token response
        with patch.object(PaypalService, '_get_access_token', return_value='test_access_token'):
            service = PaypalService()

            # Mock failed capture response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                'status': 'FAILED',
                'message': 'Payment failed'
            }
            mock_post.return_value = mock_response

            # Execute
            success, capture_data = service.process_payment(self.payment)

            # Assertions
            self.assertFalse(success)
            self.assertEqual(capture_data['status'], 'FAILED')

