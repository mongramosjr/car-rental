# bookings/test_models.py or bookings/test_serializers.py
from django.test import TestCase
from rest_framework import serializers
from django.contrib.auth import get_user_model
from overdrive.models import Booking
from fleet_management.models import Car, Manufacturer, Vehicle
from overdrive.serializers import BookingSerializer
from fleet_management.serializers import CarSerializer
import datetime
from django.utils import timezone

User = get_user_model()

class SerializerTestCase(TestCase):

    def setUp(self):
        # Example data for Car
        self.toyota = Manufacturer.objects.create(
            name="Toyota",
            country="Philippines"
        )
        
        self.car_data = {
            'license_plate': 'XYZ7890',
            'passenger_capacity':5,
            'make': self.toyota,
            'model': 'Civic',
            'year': 2023,
            'is_available': True,
            'price_per_hour': 12.50,
            'location': 'Quezon City'
        }

        self.user = User.objects.create_user(email='testuser', password='12345')

        # Create a car instance
        self.car = Car.objects.create(**self.car_data)

        # Access Car fields from Vehicle
        self.vehicle = Vehicle.objects.get(id=self.car.id)

        # Example data for Booking (assuming Booking model exists with these fields)
        self.booking_data = {
            'user': self.user,  # Assuming user with id 1 exists
            'vehicle': self.vehicle,
            'start_time': timezone.make_aware(datetime.datetime.now()),
            'end_time': timezone.make_aware(datetime.datetime.now() + datetime.timedelta(hours=1)),
            'total_price': 12.50  # Example price
        }

        # Create a booking instance (you might need to adjust this based on your model)
        self.booking = Booking.objects.create(**self.booking_data)

    def test_car_serializer(self):
        serializer = CarSerializer(instance=self.car)
        data = serializer.data

        # Check if the serialized data matches the model instance
        self.assertEqual(data['license_plate'], self.car.license_plate)
        self.assertEqual(data['passenger_capacity'], self.car.passenger_capacity)
        self.assertEqual(data['make']['id'], self.car.make.id)
        self.assertEqual(data['model'], self.car.model)
        self.assertEqual(float(data['price_per_hour']), float(self.car.price_per_hour))
        self.assertEqual(data['location'], self.car.location)
        self.assertEqual(data['is_available'], self.car.is_available)

    def test_booking_serializer(self):
        serializer = BookingSerializer(instance=self.booking)
        data = serializer.data

        # Check if the serialized data matches the model instance
        self.assertEqual(data['vehicle']['id'], self.vehicle.id)
        self.assertEqual(data['user']['id'], self.user.id)  # Assuming user_id corresponds to user field
        self.assertIn('start_time', data)
        self.assertIn('end_time', data)
        self.assertEqual(float(data['total_price']), float(self.booking.total_price))

    def test_car_serializer_validation(self):
        invalid_data = {
            'license_plate': 'XYZ7890',  # duplicate license plate
            'passenger_capacity':5,
            'make': self.toyota,
            'model': 'Civic',
            'year': 2023,
            'is_available': True,
            'price_per_hour': 12.50,
            'location': 'Quezon City'
        }
        
        serializer = CarSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('license_plate', serializer.errors)

    def test_booking_serializer_validation(self):
        # Example: Booking without required fields
        invalid_data = {
            'vehicle': self.vehicle.id,
            'start_time': datetime.datetime.now().isoformat(),
            # 'end_time' is missing
        }
        
        serializer = BookingSerializer(data=invalid_data)
        self.assertFalse(serializer.is_valid())
        self.assertIn('end_time', serializer.errors)
