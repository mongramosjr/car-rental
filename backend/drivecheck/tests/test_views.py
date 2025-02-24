from django.test import TestCase
from rest_framework.test import APIClient
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
from PIL import Image
import io

User = get_user_model()

class VerificationViewTest(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            email="test@example.com",
            phone_number="1234567890",
            user_type="customer",
            verification_method="Email"
        )
        self.user.is_active = True
        self.user.save()
        
        self.verification = UserVerification.objects.create(user=self.user)
        refresh = RefreshToken.for_user(self.user)
        self.token = str(refresh.access_token)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.token}')

        # Create a test image using PIL
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')
        self.image_content = image_io.getvalue()

        # Create a test image file
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=image_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_selfie_upload_view(self):
        url = reverse('upload_selfie')
        response = self.client.post(url, {"selfie_image": self.test_image}, format='multipart')
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["message"], "Selfie uploaded successfully")
        
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, "selfie_uploaded")
        self.assertIsNotNone(self.verification.selfie_image)

    def test_id_card_upload_view(self):
        self.verification.status = "selfie_uploaded"
        self.verification.save()
        
        url = reverse('upload_id')
        response = self.client.post(url, {"id_card_image": self.test_image}, format='multipart')
        
        self.assertEqual(response.status_code, 200)
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, "id_uploaded")

    def test_selfie_with_id_upload_view(self):
        self.verification.status = "id_uploaded"
        self.verification.save()
        
        url = reverse('upload_selfie_with_id')
        response = self.client.post(url, {"selfie_with_id_image": self.test_image}, format='multipart')
        
        self.assertEqual(response.status_code, 200)
        self.user.refresh_from_db()
        self.verification.refresh_from_db()
        self.assertEqual(self.verification.status, "selfie_with_id_uploaded")
        self.assertTrue(self.user.is_verified)

    def test_verification_status_view(self):
        url = reverse('verification_status')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "pending")

    def test_get_decrypted_image_view(self):
        # Upload an encrypted selfie first
        serializer = SelfieUploadSerializer(instance=self.verification, data={"selfie_image": self.test_image})
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        url = reverse('get_decrypted_image', kwargs={'image_type': 'selfie'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.content, self.image_content)  # Decrypted content matches original

    def test_unauthenticated_access(self):
        self.client.credentials()  # Remove authentication
        url = reverse('upload_selfie')
        response = self.client.post(url)
        
        self.assertEqual(response.status_code, 401)

    def tearDown(self):
        if self.verification.selfie_image:
            self.verification.selfie_image.delete()
        if self.verification.id_card_image:
            self.verification.id_card_image.delete()
        if self.verification.selfie_with_id_image:
            self.verification.selfie_with_id_image.delete()
