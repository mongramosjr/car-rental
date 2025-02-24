from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from drivecheck.models import UserVerification
from drivecheck.serializers import (
    SelfieUploadSerializer,
    IDCardUploadSerializer,
    SelfieWithIDSerializer,
    VerificationStatusSerializer
)
from django.urls import reverse
import io

User = get_user_model()

class UserVerificationModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@model.com",
            password="testpass123",
            phone_number="1234567890",
            verification_method="Email",
            user_type="customer"
        )
        self.verification = UserVerification.objects.create(user=self.user)

    def test_model_creation(self):
        self.assertEqual(self.verification.user, self.user)
        self.assertEqual(self.verification.status, "pending")
        self.assertFalse(self.verification.selfie_image)
        self.assertFalse(self.verification.selfie_image.name)
        self.assertFalse(self.verification.id_card_image)
        self.assertFalse(self.verification.id_card_image.name)
        self.assertFalse(self.verification.selfie_with_id_image)
        self.assertFalse(self.verification.selfie_with_id_image.name)
        self.assertTrue(self.verification.__str__(), f"Verification for {self.user.email}")

    def test_encryption_key_generation(self):
        key = self.verification.generate_encryption_key()
        self.assertIsNotNone(self.verification.encryption_key)
        self.assertTrue(len(self.verification.encryption_key) > 0)

    def test_encrypt_decrypt_image(self):
        image_content = b"fake image data"
        image_file = SimpleUploadedFile("test.jpg", image_content, content_type="image/jpeg")
        
        encrypted_file = self.verification.encrypt_image(image_file)
        self.assertNotEqual(encrypted_file.read(), image_content)  # Ensure it's encrypted
        
        decrypted_content = self.verification.decrypt_image(encrypted_file)
        self.assertEqual(decrypted_content, image_content)  # Ensure it decrypts back correctly

    def tearDown(self):
        if self.verification.selfie_image:
            self.verification.selfie_image.delete()
        if self.verification.id_card_image:
            self.verification.id_card_image.delete()
        if self.verification.selfie_with_id_image:
            self.verification.selfie_with_id_image.delete()

