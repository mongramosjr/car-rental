from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient
from django.contrib.auth import get_user_model
from authdrive.models import OTP
from authdrive.views import RegisterView, OTPVerificationView
import pyotp

User = get_user_model()

class CustomUserModelTest(TestCase):
    def test_create_user(self):
        user = User.objects.create_user(
            email="test@model.com",
            password="testpass123",
            phone_number="1234567890",
            verification_method="Email",
            user_type="customer"
        )
        self.assertEqual(user.email, "test@model.com")
        self.assertEqual(user.user_type, "customer")
        self.assertEqual(user.phone_number, "1234567890")
        self.assertFalse(user.is_active)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_create_superuser(self):
        admin_user = User.objects.create_superuser(
            email="admin",
            password="adminpass123"
        )
        self.assertEqual(admin_user.email, "admin")
        self.assertTrue(admin_user.is_active)
        self.assertTrue(admin_user.is_staff)
        self.assertTrue(admin_user.is_superuser)
