from django.test import TestCase
from django.contrib.auth import get_user_model
from payment.services import CashService
from overdrive.models import Booking
from payment.models import BookingPayment
from payment.cash_payment import CashBookingPayment
from fleet_management.models import Car, Owner, Manufacturer

User = get_user_model()


class CashServiceTestCase(TestCase):

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
        
        self.payment = CashBookingPayment.objects.create(
            booking=self.booking,
            amount=240.00,
            method='cash',
            status='pending'
        )
        self.cash_service = CashService()

    def test_process_payment_success(self):
        # Cash payment doesn't involve real-time processing, so we just test if the method returns True
        success = self.cash_service.process_payment(self.payment)
        self.assertTrue(success)
        self.payment.refresh_from_db()
        self.assertEqual(self.payment.transaction_id, "CASH-PAYMENT-MOCK")  # Or whatever mock you set

    def test_process_payment_failure(self):
        # Here you would mock or setup a condition where the payment fails
        # Since we don't have actual GCash API integration, we can't simulate failure
        pass  # For now, it's a placeholder
