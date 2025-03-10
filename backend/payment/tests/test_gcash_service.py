from django.test import TestCase
from django.contrib.auth import get_user_model
from payment.services import GcashService
from overdrive.models import Booking
from payment.models import BookingPayment
from payment.gcash_payment import GcashBookingPayment
from fleet_management.models import Car, Owner, Manufacturer, Vehicle

User = get_user_model()



class GcashServiceTestCase(TestCase):

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
        self.payment = GcashBookingPayment.objects.create(
            booking=self.booking,
            amount=240.00,
            method='gcash',
            status='pending'
        )
        self.gcash_service = GcashService()


    def test_process_payment_success(self):
        success = self.gcash_service.process_payment(self.payment)
        self.assertTrue(success)
        self.payment.refresh_from_db()  # Refresh from DB to check updates
        self.assertEqual(self.payment.transaction_id, "GCASH-TRANSACTION-MOCK")
        self.assertEqual(self.payment.status, "pending")  # Status remains 'pending' as we didn't change it in GCashService

    def test_process_payment_failure(self):
        # Here you would mock or setup a condition where the payment fails
        # Since we don't have actual GCash API integration, we can't simulate failure
        pass  # For now, it's a placeholder
