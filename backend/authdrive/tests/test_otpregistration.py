from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from authdrive.models import OTP
from authdrive.views import RegisterView, OTPVerificationView
import pyotp
import json

User = get_user_model()

class CarRentalUserRegistrationTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.register_url = reverse('user-register')
        self.verify_otp_url = reverse('verify-otp')

    def test_user_registration_with_email(self):
        data = {
            'email': 'test@registration.com',
            # 'phone_number': '1234567890',
            'password': 'password123',
            'verification_method': 'Email',
            'user_type': 'customer'
        }
        response = self.client.post(self.register_url, data, format='json')

        print(json.dumps(response.data, indent=2))
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(User.objects.count(), 1)
        self.assertEqual(OTP.objects.count(), 1)  # Check if OTP was created
        self.assertFalse(User.objects.get(email='test@registration.com').is_active)  # User should not be active yet

    def test_user_registration_with_sms(self):
        data = {
            # 'email': 'test_sms@registration.com',
            'phone_number': '1234567891',
            'password': 'password123',
            'verification_method': 'SMS',
            'user_type': 'customer'
        }
        # response = self.client.post(self.register_url, data, format='json')
        
        # self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        # self.assertEqual(User.objects.count(), 1)
        # self.assertEqual(OTP.objects.count(), 1)  # Check if OTP was created
        # self.assertFalse(User.objects.get(email='test_sms@registration.com').is_active)  # User should not be active yet

    def test_user_registration_invalid_method(self):
        data = {
            'email': 'invalid@registration.com',
            'phone_number': '1234567892',
            'password': 'password123',
            'verification_method': 'Invalid',
            'user_type': 'customer'
        }
        response = self.client.post(self.register_url, data, format='json')
        print(json.dumps(response.data, indent=2))
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_otp_verification(self):
        # First, register a user
        user_data = {
            'email': 'otp_test@registration.com',
            # 'phone_number': '1234567893',
            'password': 'password123',
            'verification_method': 'Email',
            'user_type': 'customer'
        }
        self.client.post(self.register_url, user_data, format='json')
        
        user = User.objects.get(email='otp_test@registration.com')
        otp = OTP.objects.get(user=user).otp
        
        verify_data = {
            'otp': otp,
            'email_or_phone': 'otp_test@registration.com'
        }
        response = self.client.post(self.verify_otp_url, verify_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(User.objects.get(email='otp_test@registration.com').is_active)

    def test_otp_verification_invalid(self):
        # Register user
        user_data = {
            'email': 'invalid_otp@registration.com',
            'phone_number': '1234567894',
            'password': 'password123',
            'verification_method': 'Email',
            'user_type': 'customer'
        }
        self.client.post(self.register_url, user_data, format='json')
        
        verify_data = {
            'otp': '123456',  # Invalid OTP
            'email_or_phone': 'invalid_otp@registration.com'
        }
        response = self.client.post(self.verify_otp_url, verify_data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
