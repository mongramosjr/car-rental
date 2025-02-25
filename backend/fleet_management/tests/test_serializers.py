from django.test import TestCase
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.utils import timezone
import datetime
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from rest_framework_simplejwt.tokens import RefreshToken
import json
from fleet_management.models import Manufacturer, Owner, Car
from fleet_management.serializers import CarSerializer

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
            'make': self.toyota,
            'model': 'Civic',
            'year': 2023,
            'is_available': True,
            'price_per_hour': 12.50,
            'location': 'Quezon City'
        }

        self.user = User.objects.create_user(email='testuser', password='12345')
        self.user.is_active = True
        self.user.save()

        # Create a car instance
        self.car = Car.objects.create(**self.car_data)

    def test_car_serializer(self):
        serializer = CarSerializer(instance=self.car)
        data = serializer.data

        # Check if the serialized data matches the model instance
        self.assertEqual(data['license_plate'], self.car.license_plate)
        self.assertEqual(data['make']['id'], self.car.make.id)
        self.assertEqual(data['model'], self.car.model)
        self.assertEqual(float(data['price_per_hour']), float(self.car.price_per_hour))
        self.assertEqual(data['location'], self.car.location)
        self.assertEqual(data['is_available'], self.car.is_available)

    def test_car_serializer_validation(self):
        invalid_data = {
            'license_plate': 'XYZ7890',  # duplicate license plate
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
