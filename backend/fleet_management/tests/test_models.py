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

class CarModelTest(TestCase):

    def setUp(self):
        self.toyota = Manufacturer.objects.create(
            name="Toyota",
            country="Philippines"
        )
        self.honda = Manufacturer.objects.create(
            name="Honda",
            country="Philippines"
        )

        Car.objects.create(
            license_plate="ABC1234",
            passenger_capacity=5,
            make=self.toyota,
            model="Corolla",
            year=2022,
            price_per_hour=10.00,
            location="Manila",
        )

    def test_car_creation(self):
        car = Car.objects.get(id=1)
        self.assertEqual(car.make, self.toyota)
        self.assertEqual(car.model, "Corolla")
        self.assertEqual(car.year, 2022)
        self.assertTrue(car.is_available)  # default should be True

    def test_year_validators(self):
        current_year = timezone.now().year
        # Test lower bound
        car = Car(license_plate="XYZ9876", make=self.honda, model="Civic", year=1977, price_per_hour=15.00, location="Cebu")
        with self.assertRaises(ValidationError):
            car.full_clean()
        # Test upper bound
        car = Car(license_plate="XYZ9877", make=self.honda, model="Civic", year=current_year + 1, price_per_hour=15.00, location="Cebu")
        with self.assertRaises(ValidationError):
            car.full_clean()

    def test_string_representation(self):
        car = Car.objects.get(id=1)
        self.assertEqual(str(car), "Toyota Corolla 2022")

