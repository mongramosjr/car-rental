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


class CarAPITestCase(APITestCase):
    def setUp(self):
        # Create test data
        self.client = APIClient()
        
        # Create manufacturer
        self.manufacturer = Manufacturer.objects.create(name="Honda", country="Japan")
        
        # Create regular user and owner
        self.user = User.objects.create_user(email='testuser', password='testpass123')
        self.user.is_active = True
        self.user.save()
        self.owner = Owner.objects.create(user=self.user, name="Test Owner")
        
        # Create another user for testing permissions
        self.other_user = User.objects.create_user(email='otheruser', password='testpass123')
        self.other_user.is_active = True
        self.other_user.save()
        self.other_owner = Owner.objects.create(user=self.other_user, name="Other Owner")
        
        # Create test car
        self.car = Car.objects.create(
            owner=self.owner,
            passenger_capacity=5,
            license_plate="XYZ789",
            make=self.manufacturer,
            model="Civic",
            year=2021,
            price_per_hour=15.00,
            location={"lat": 40.7128, "lng": -74.0060}
        )
        
        # Get JWT token for authenticated requests
        self.token = str(RefreshToken.for_user(self.user).access_token)
        self.other_token = str(RefreshToken.for_user(self.other_user).access_token)

    def test_get_car_list_public(self):
        """Test retrieving list of available cars without authentication"""
        response = self.client.get('/api/cars/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]['license_plate'], 'XYZ789')

    def test_get_car_detail_public(self):
        """Test retrieving car details without authentication"""
        response = self.client.get(f'/api/cars/{self.car.id}/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['model'], 'Civic')
        self.assertEqual(float(response.data['price_per_hour']), 15.00)

    def test_create_car_authenticated(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'license_plate': 'DEF456',
            'passenger_capacity':5,
            'make_id': self.manufacturer.id,
            'owner_id': self.owner.id,
            'model': 'Accord',
            'year': 2022,
            'price_per_hour': 20.00,
            'location': {'lat': 34.0522, 'lng': -118.2437}
        }
        response = self.client.post('/api/cars/create/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(Car.objects.count(), 2)
        self.assertEqual(response.data['model'], 'Accord')

    def test_create_car_unauthenticated(self):
        """Test creating a car without authentication should fail"""
        data = {
            'license_plate': 'GHI789',
            'passenger_capacity':5,
            'make_id': self.manufacturer.id,
            'model': 'CR-V',
            'year': 2023,
            'price_per_hour': 25.00
        }
        response = self.client.post('/api/cars/create/', data, format='json')
        # print(f"Response status: {response.status_code}")
        # print(f"Response data: {json.dumps(response.data, indent=2)}")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_update_car_own_vehicle(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'price_per_hour': 18.50,
            'is_available': False
        }
        response = self.client.put(f'/api/cars/{self.car.id}/update/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.car.refresh_from_db()
        self.assertEqual(float(self.car.price_per_hour), 18.50)
        self.assertFalse(self.car.is_available)

    def test_update_car_other_owner(self):
        """Test updating someone else's car should fail"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.other_token}')
        data = {
            'price_per_hour': 20.00
        }
        response = self.client.put(f'/api/cars/{self.car.id}/update/', data, format='json')
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_get_unavailable_car(self):
        """Test that unavailable cars aren't accessible publicly"""
        self.car.is_available = False
        self.car.save()
        
        response = self.client.get(f'/api/cars/{self.car.id}/')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_price_validation(self):
        """Test that negative price is rejected"""
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')
        data = {
            'license_plate': 'JKL012',
            'passenger_capacity':5,
            'make_id': self.manufacturer.id,
            'owner_id': self.owner.id,
            'model': 'Pilot',
            'year': 2022,
            'price_per_hour': -5.00
        }
        response = self.client.post('/api/cars/create/', data, format='json')
        print(f"Response data: {json.dumps(response.data, indent=2)}")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
