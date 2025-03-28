# bookings/test_views.py
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient, APITestCase
from rest_framework_simplejwt.tokens import RefreshToken
import datetime
from django.utils import timezone
from django.contrib.auth import get_user_model
from overdrive.models import Booking
from fleet_management.models import Car, Manufacturer, Vehicle, Owner
import json

User = get_user_model()

class CarViewTest(APITestCase):

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(email='testuser@mail.com', password='12345')
        self.user.is_active = True
        self.user.save()
        self.toyota = Manufacturer.objects.create(
            name="Toyota",
            country="Philippines"
        )
        self.car = Car.objects.create(
            license_plate="ABC1234",
            passenger_capacity=5,
            make=self.toyota,
            model="Corolla",
            year=2022,
            price_per_hour=10.00,
            location="Manila",
        )
        self.car2 = Car.objects.create(
            license_plate="ABC5678",
            passenger_capacity=5,
            make=self.toyota,
            model="Vios",
            year=2020,
            is_available=False,  # Not available, should not appear
            price_per_hour=40.00,
            location="Quezon City",
        )

        # Access Car fields from Vehicle
        self.vehicle = Vehicle.objects.get(id=self.car.id)
        self.vehicle2 = Vehicle.objects.get(id=self.car2.id)

        self.booking = Booking.objects.create(
            user=self.user,
            vehicle=self.vehicle,
            start_time=timezone.make_aware(datetime.datetime.now() - datetime.timedelta(days=11)),
            end_time=timezone.make_aware(datetime.datetime.now() - datetime.timedelta(days=10) + datetime.timedelta(hours=24)),
            total_price=480.0
        )

    def refresh_token(self):
        # Generate JWT token for the user
        refresh = RefreshToken.for_user(self.user)
        return str(refresh.access_token)

    def test_car_list_view(self):
        self.client.credentials()
        
        url = reverse('car-list')
        response = self.client.get(url)
        print(json.dumps(response.data, indent=2))
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)  # We have only one car

    def test_create_booking_unauthenticated(self):
        url = reverse('create-booking')
        data = {
            'vehicle': self.vehicle.id,
            'start_time': timezone.make_aware(datetime.datetime.now()  - datetime.timedelta(days=2)).isoformat(),
            'end_time': timezone.make_aware(datetime.datetime.now() - datetime.timedelta(days=2) + datetime.timedelta(hours=24)).isoformat(),
        }
        response = self.client.post(url, data, format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)  # Should fail without authentication

    def test_create_booking_view(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_token()}')

        url = reverse('create-booking')
        data = {
            'user_id': self.user.id,
            'vehicle_id': self.vehicle.id,
            'start_time': timezone.make_aware(datetime.datetime.now() - datetime.timedelta(days=5)).isoformat(),
            'end_time': timezone.make_aware(datetime.datetime.now() - datetime.timedelta(days=4) + datetime.timedelta(hours=24)).isoformat(),
        }
        # response = self.client.post(url, data, format='json')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('id', response.data)  # Check if a booking was created
        self.assertEqual(Booking.objects.count(), 2)
        booking = Booking.objects.all()[1]
        self.assertEqual(booking.total_price, 480.00)  # 1 hour * $15/hour


    def test_create_overlapping_booking_view(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.refresh_token()}')
        self.booking.status = "confirmed"
        self.booking.save()
        url = reverse('create-booking')
        data = {
            'user': self.user.id,
            'vehicle_id': self.vehicle.id,
            'start_time': timezone.make_aware(datetime.datetime.now() - datetime.timedelta(days=10)).isoformat(),
            'end_time': timezone.make_aware(datetime.datetime.now() - datetime.timedelta(days=10) + datetime.timedelta(hours=3)).isoformat(),
        }
        response = self.client.post(url, data, format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class BaseBookingAPITest(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.customer = User.objects.create_user(email='customer@mail.com', password='testpass', user_type='customer')
        self.customer.is_active = True
        self.customer.save()
        self.owner = User.objects.create_user(email='owner@mail.com', password='testpass', user_type='car_owner')
        self.owner.is_active = True
        self.owner.save()

        self.car_owner = Owner.objects.create(user=self.owner, name='Owner Carlota')
        self.toyota = Manufacturer.objects.create(
            name="Toyota",
            country="Philippines"
        )
        self.car = Car.objects.create(
            owner=self.car_owner,
            license_plate="XYZ987",
            passenger_capacity=5,
            make=self.toyota,
            model='TestModel',
            year=2024,
            price_per_hour=10.0,
            is_available=True,
            location="Manila",
        )
        # Access Car fields from Vehicle
        self.vehicle = Vehicle.objects.get(id=self.car.id)
        
        self.booking = Booking.objects.create(
            user=self.customer,
            vehicle=self.vehicle,
            start_time=timezone.make_aware(datetime.datetime.now()),
            end_time=timezone.make_aware(datetime.datetime.now() + datetime.timedelta(hours=1)),
            total_price=10.0
        )

        # Generate JWT token for the user
        refresh = RefreshToken.for_user(self.customer)
        self.customer_token = str(refresh.access_token)
        # Generate JWT token for the car owner
        refresh = RefreshToken.for_user(self.owner)
        self.owner_token = str(refresh.access_token)


class CreateBookingAPITest(BaseBookingAPITest):
    def test_create_booking(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.customer_token}')
        data = {
            'user_id': self.customer.id,
            'vehicle_id': self.vehicle.id,
            'start_time': timezone.make_aware(datetime.datetime.now() + datetime.timedelta(days=2)).isoformat(),
            'end_time': timezone.make_aware(datetime.datetime.now() + datetime.timedelta(days=2) + datetime.timedelta(hours=1)).isoformat()
        }
        print("test_create_booking")
        print(data)

        response = self.client.post('/api/bookings/', data, format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Booking.objects.filter(user=self.customer, vehicle=self.vehicle).exists())

    def test_create_booking_with_invalid_user(self):
        user = User.objects.create_user(email='admin@mail.com', password='testpass', user_type='admin')
        user.is_active = True
        user.save()
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.customer_token}')
        data = {
            'user_id': user.id,
            'vehicle_id': self.vehicle.id,
            'start_time': timezone.make_aware(datetime.datetime.now() + datetime.timedelta(days=4)).isoformat(),
            'end_time': timezone.make_aware(datetime.datetime.now() + datetime.timedelta(days=4) + datetime.timedelta(hours=1)).isoformat()
        }
        print("test_create_booking_with_invalid_user")
        print(data)
        response = self.client.post('/api/bookings/', data, format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class CancelBookingAPITest(BaseBookingAPITest):
    def test_cancel_booking_by_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.post(f'/api/bookings/cancel/{self.booking.id}/', format='json')
        print(json.dumps(response.data, indent=2))  # This will print the error messages if any
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Booking.objects.get(id=self.booking.id).status, 'canceled')

    def test_cancel_booking_by_customer(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.customer_token}')
        response = self.client.post(f'/api/bookings/cancel/{self.booking.id}/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Booking.objects.get(id=self.booking.id).status, 'canceled')

    def test_cancel_booking_by_unrelated_user(self):
        unrelated_user = User.objects.create_user(email='unrelated@mail.com', password='testpass', user_type='customer')
        response = self.client.post(f'/api/bookings/cancel/{self.booking.id}/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_cancel_non_existent_booking(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.customer_token}')
        response = self.client.post('/api/bookings/cancel/9999/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class ConfirmBookingAPITest(BaseBookingAPITest):
    def test_confirm_booking_by_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.post(f'/api/bookings/confirm/{self.booking.id}/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Booking.objects.get(id=self.booking.id).status, 'confirmed')

    def test_confirm_booking_by_customer(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.customer_token}')
        response = self.client.post(f'/api/bookings/confirm/{self.booking.id}/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_confirm_non_existent_booking(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.post('/api/bookings/confirm/9999/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


class RentedBookingAPITest(BaseBookingAPITest):
    def test_rent_booking_by_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.post(f'/api/bookings/delivered/{self.booking.id}/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Booking.objects.get(id=self.booking.id).status, 'rented')

    def test_rent_booking_by_customer(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.customer_token}')
        response = self.client.post(f'/api/bookings/delivered/{self.booking.id}/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class StartDrivingAPITest(BaseBookingAPITest):
    def test_start_driving_by_customer(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.customer_token}')
        response = self.client.post(f'/api/bookings/start_driving/{self.booking.id}/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Booking.objects.get(id=self.booking.id).status, 'driving')

    def test_start_driving_by_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.post(f'/api/bookings/start_driving/{self.booking.id}/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)


class ReturnCarAPITest(BaseBookingAPITest):
    def test_return_car_by_owner(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.post(f'/api/bookings/return_car/{self.booking.id}/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(Booking.objects.get(id=self.booking.id).status, 'returned')

    def test_return_car_by_customer(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.customer_token}')
        response = self.client.post(f'/api/bookings/return_car/{self.booking.id}/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

class BookingDetailAPITest(BaseBookingAPITest):
    def test_booking_details(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.owner_token}')
        response = self.client.get(f'/api/bookings/{self.booking.id}/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_booking_details_non_existent(self):
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.customer_token}')
        response = self.client.get(f'/api/bookings/2/', format='json')
        print(json.dumps(response.data, indent=2))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)