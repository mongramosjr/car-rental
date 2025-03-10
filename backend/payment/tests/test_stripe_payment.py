from django.test import TestCase
from django.utils import timezone
from django.contrib.auth import get_user_model
from django.db.models import Q
from overdrive.models import Booking
from payment.models import BookingPayment
from payment.services import StripeService
from payment.stripe_payment import StripeBookingPayment
from fleet_management.models import Car, Owner, Manufacturer, Vehicle
import json

User = get_user_model()


class StripeBookingPaymentTest(TestCase):
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
            total_price=50,
            status='confirmed'
        )
        self.payment = StripeBookingPayment(
            booking=self.booking,
            amount=50.00,
            method='stripe',
            status='pending',
            created_at=timezone.now()
        )


    def test_model_instantiation(self):
        """Test that StripeBookingPayment can be instantiated correctly"""
        self.assertEqual(self.payment.amount, 50.00)
        self.assertEqual(self.payment.method, 'stripe')
        self.assertEqual(self.payment.status, 'pending')
        self.assertIsNone(self.payment.stripe_payment_intent_id)
        self.assertIsNone(self.payment.client_secret)
        self.assertIsNone(self.payment.payment_method)
        self.assertIsNone(self.payment.charge_id)
        self.assertIsNone(self.payment.metadata)

    def test_set_and_get_metadata(self):
        """Test setting and getting metadata JSON data"""
        metadata_data = {
            'order_id': 'ORD-123',
            'customer_id': 'CUST-456'
        }
        self.payment.set_metadata(metadata_data)
        self.assertEqual(self.payment.metadata, json.dumps(metadata_data))
        retrieved_metadata = self.payment.get_metadata()
        self.assertEqual(retrieved_metadata, metadata_data)

    def test_none_metadata(self):
        """Test handling of None value in metadata"""
        self.payment.set_metadata(None)
        self.assertIsNone(self.payment.metadata)
        self.assertIsNone(self.payment.get_metadata())

    def test_stripe_specific_fields(self):
        """Test setting and retrieving Stripe-specific fields"""
        self.payment.stripe_payment_intent_id = 'pi_123456789'
        self.payment.client_secret = 'secret_abcdef123'
        self.payment.payment_method = 'pm_card_visa'
        self.payment.charge_id = 'ch_987654321'
        
        self.assertEqual(self.payment.stripe_payment_intent_id, 'pi_123456789')
        self.assertEqual(self.payment.client_secret, 'secret_abcdef123')
        self.assertEqual(self.payment.payment_method, 'pm_card_visa')
        self.assertEqual(self.payment.charge_id, 'ch_987654321')

    def test_stripe_booking_payment_save_new(self):
        # Test saving a new StripeBookingPayment instance
        stripe_payment = StripeBookingPayment(
            booking=self.booking,
            amount=200.75,
            transaction_id='txn_987',
            status='pending',
            stripe_payment_intent_id='pi_123',
            client_secret='secret_456',
        )
        stripe_payment.save()

        # Refresh from DB
        stripe_payment.refresh_from_db()

        # Assertions
        self.assertEqual(stripe_payment.method, 'stripe')  # method forced to 'stripe'
        self.assertEqual(stripe_payment.amount, 200.75)
        self.assertEqual(stripe_payment.transaction_id, 'txn_987')
        self.assertEqual(stripe_payment.status, 'pending')
        self.assertEqual(stripe_payment.stripe_payment_intent_id, 'pi_123')
        self.assertEqual(stripe_payment.client_secret, 'secret_456')

    def test_stripe_booking_payment_save_update(self):
        # Test updating an existing StripeBookingPayment instance
        stripe_payment = StripeBookingPayment.objects.create(
            booking=self.booking,
            amount=150.00,
            method='some_other_method',  # Initially set to something else
        )
        stripe_payment.amount = 175.00
        stripe_payment.save()

        # Refresh from DB
        stripe_payment.refresh_from_db()

        # Assertions
        self.assertEqual(stripe_payment.method, 'stripe')  # method overridden to 'stripe'
        self.assertEqual(stripe_payment.amount, 175.00)

    def test_booking_payment_base_save(self):
        # Test that BookingPayment itself can save without forcing method
        base_payment = BookingPayment(
            booking=self.booking,
            amount=300.00,
            method='manual',  # Arbitrary method
            transaction_id='txn_manual',
        )
        base_payment.save()

        # Refresh from DB
        base_payment.refresh_from_db()

        # Assertions
        self.assertEqual(base_payment.method, 'manual')  # method unchanged
        self.assertEqual(base_payment.amount, 300.00)