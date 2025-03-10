from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
from overdrive.models import Booking
from payment.models import BookingPayment
from payment.services import PaypalService
from payment.paypal_payment import PayPalBookingPayment
from fleet_management.models import Car, Owner, Manufacturer, Vehicle
import json

User = get_user_model()


class PayPalBookingPaymentTest(TestCase):
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
        # Create a base BookingPayment instance for testing PayPal extension
        self.payment = PayPalBookingPayment(
            booking=self.booking,
            amount=240.00,
            method='paypal',
            status='pending',
            created_at=timezone.now()
        )


    def test_model_instantiation(self):
        """Test that PayPalBookingPayment can be instantiated correctly"""
        self.assertEqual(self.payment.amount, 240.00)
        self.assertEqual(self.payment.method, 'paypal')
        self.assertEqual(self.payment.status, 'pending')
        self.assertIsNone(self.payment.paypal_request_id)
        self.assertIsNone(self.payment.order_id)
        self.assertIsNone(self.payment.payer)
        self.assertIsNone(self.payment.payment_source)
        self.assertIsNone(self.payment.links)

    def test_set_and_get_payer(self):
        """Test setting and getting payer JSON data"""
        payer_data = {
            'name': {'given_name': 'John', 'surname': 'Doe'},
            'email_address': 'john.doe@example.com'
        }
        self.payment.set_payer(payer_data)
        self.assertEqual(self.payment.payer, json.dumps(payer_data))
        retrieved_payer = self.payment.get_payer()
        self.assertEqual(retrieved_payer, payer_data)

    def test_set_and_get_payment_source(self):
        """Test setting and getting payment source JSON data"""
        source_data = {
            'paypal': {'experience_context': {'payment_method_preference': 'IMMEDIATE'}}
        }
        self.payment.set_payment_source(source_data)
        self.assertEqual(self.payment.payment_source, json.dumps(source_data))
        retrieved_source = self.payment.get_payment_source()
        self.assertEqual(retrieved_source, source_data)

    def test_set_and_get_links(self):
        """Test setting and getting links JSON data"""
        links_data = {
            'self': 'https://api.paypal.com/v2/checkout/orders/123',
            'approve': 'https://www.paypal.com/checkoutnow?token=123'
        }
        self.payment.set_links(links_data)
        self.assertEqual(self.payment.links, json.dumps(links_data))
        retrieved_links = self.payment.get_links()
        self.assertEqual(retrieved_links, links_data)

    def test_none_values(self):
        """Test handling of None values in JSON fields"""
        self.payment.set_payer(None)
        self.assertIsNone(self.payment.payer)
        self.assertIsNone(self.payment.get_payer())
        
        self.payment.set_payment_source(None)
        self.assertIsNone(self.payment.payment_source)
        self.assertIsNone(self.payment.get_payment_source())
        
        self.payment.set_links(None)
        self.assertIsNone(self.payment.links)
        self.assertIsNone(self.payment.get_links())

    def test_paypal_booking_payment_save_new(self):
        # Test saving a new PayPalBookingPayment instance
        paypal_payment = PayPalBookingPayment(
            booking=self.booking,
            amount=100.50,
            transaction_id='txn_123',
            status='completed',
            paypal_request_id='req_456',
            order_id='order_789',
        )
        paypal_payment.save()

        # Refresh from DB to ensure saved values
        paypal_payment.refresh_from_db()

        # Assertions
        self.assertEqual(paypal_payment.method, 'paypal')  # method forced to 'paypal'
        self.assertEqual(paypal_payment.amount, 100.50)
        self.assertEqual(paypal_payment.transaction_id, 'txn_123')
        self.assertEqual(paypal_payment.status, 'completed')
        self.assertEqual(paypal_payment.paypal_request_id, 'req_456')
        self.assertEqual(paypal_payment.order_id, 'order_789')

    def test_paypal_booking_payment_save_update(self):
        # Test updating an existing PayPalBookingPayment instance
        paypal_payment = PayPalBookingPayment.objects.create(
            booking=self.booking,
            amount=50.00,
            method='some_other_method',  # Initially set to something else
        )
        paypal_payment.amount = 75.00
        paypal_payment.save()

        # Refresh from DB
        paypal_payment.refresh_from_db()

        # Assertions
        self.assertEqual(paypal_payment.method, 'paypal')  # method overridden to 'paypal'
        self.assertEqual(paypal_payment.amount, 75.00)