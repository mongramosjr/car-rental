from django.test import TestCase
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock

from payment.views import ProcessPaymentView
from payment.services import get_payment_service
from overdrive.models import Booking
from payment.models import BookingPayment
from fleet_management.models import Car, Owner, Manufacturer
from payment.services import get_payment_service, GcashService, PaypalService, StripeService, CashService

User = get_user_model()

class PaymentViewTestCase(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='testuser@payment.com', password='12345')
        self.user.is_active = True
        self.user.save()
        
        self.car_owner = User.objects.create_user(email='testcarowner@payment.com', password='12345')
        self.car_owner.is_active = True
        self.car_owner.save()
        self.owner = Owner.objects.create(name="Test Owner", user=self.car_owner)
        self.refresh = RefreshToken.for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh.access_token}')
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

    @patch.object(GcashService, 'process_payment')
    @patch.object(PaypalService, 'process_payment')
    @patch.object(StripeService, 'process_payment')
    @patch.object(CashService, 'process_payment')
    def test_process_payment_with_all_services(self, mock_cash_process, mock_stripe_process, mock_paypal_process, mock_gcash_process):
        # Mocking the process_payment methods of all services to return True
        mock_gcash_process.return_value = True
        mock_paypal_process.return_value = True
        mock_stripe_process.return_value = True
        mock_cash_process.return_value = True
        
        # Test data for each payment method
        payment_methods = ['gcash', 'cash', 'paypal', 'stripe']
        
        for method in payment_methods:
            # Create a payment object
            BookingPayment.objects.create(
                booking=self.booking,
                amount=240.00,
                method=method,
                status='pending'
            )
            
            # Mock get_payment_service to return MagicMock with process_payment method
            with patch('payment.views.get_payment_service', side_effect=lambda m: {
                'gcash': GcashService,
                'paypal': PaypalService,
                'stripe': StripeService,
                'cash': CashService
            }.get(m)):
                response = self.client.post(f'/api/payment/{self.booking.id}/', {
                    'amount': '240.00',
                    'method': method
                }, format='json')
                
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.data, {"status": "Payment processed successfully"})

                # Check if the mock was called
                if method == 'gcash':
                    mock_gcash_process.assert_called_once()
                elif method == 'paypal':
                    mock_paypal_process.assert_called_once()
                elif method == 'stripe':
                    mock_stripe_process.assert_called_once()
                else:  # cash
                    mock_cash_process.assert_called_once()
                    
                # Reset mock calls for the next iteration
                mock_gcash_process.reset_mock()
                mock_paypal_process.reset_mock()
                mock_stripe_process.reset_mock()
                mock_cash_process.reset_mock()

    def test_invalid_payment_method(self):
        response = self.client.post(f'/api/payment/{self.booking.id}/', {
            'amount': '240.00',
            'method': 'invalid_method'
        }, format='json')
        self.assertEqual(response.status_code, 400)
        self.assertIn('method', response.data)  # Check if 'method' is in the error details
        #self.assertEqual(response.data, {"status": "Invalid payment method"})
