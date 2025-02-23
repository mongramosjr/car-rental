# bookings/test_models.py
from django.test import TestCase
from .models import Car, Manufacturer
from .serializers import CarSerializer
from django.utils import timezone
import datetime
from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError

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
        self.assertEqual(data['make'], self.car.make.id)
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
