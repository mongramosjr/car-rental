from django.test import TestCase, Client
from django.core.files.uploadedfile import SimpleUploadedFile
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.exceptions import ValidationError
from django.urls import reverse
from PIL import Image
import io
from drivecheck.models import UserVerification
from drivecheck.serializers import (
    SelfieUploadSerializer,
    IDCardUploadSerializer,
    SelfieWithIDSerializer,
    VerificationStatusSerializer
)


User = get_user_model()

class VerificationSerializerTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email="test@serializers.com",
            password="testpass123",
            phone_number="1234567890",
            verification_method="Email",
            user_type="customer"
        )
        self.verification = UserVerification.objects.create(user=self.user)

        # Create a test image using PIL
        image = Image.new('RGB', (100, 100), color='red')
        image_io = io.BytesIO()
        image.save(image_io, format='JPEG')

        # Create a test image file
        self.test_image = SimpleUploadedFile(
            name='test_image.jpg',
            content=image_io.getvalue(),
            content_type='image/jpeg'
        )

    def test_selfie_upload_serializer_validation(self):
        # Test empty data
        empty_serializer = SelfieUploadSerializer(
            instance=self.verification,
            data={}
        )
        self.assertFalse(empty_serializer.is_valid())
        self.assertIn('non_field_errors', empty_serializer.errors)

        # Test valid data
        data = {'selfie_image': self.test_image}
        serializer = SelfieUploadSerializer(
            instance=self.verification,
            data=data,
            partial=True
        )
        
        valid = serializer.is_valid()
        if not valid:
            print("Validation errors:", serializer.errors)
            
        self.assertTrue(valid)

    def test_selfie_upload_serializer_update(self):
        data = {'selfie_image': self.test_image}
        serializer = SelfieUploadSerializer(
            instance=self.verification,
            data=data,
            partial=True
        )
        
        self.assertTrue(serializer.is_valid())
        updated_instance = serializer.save()
        self.assertIsNotNone(updated_instance.selfie_image)

    def test_id_card_upload_serializer_validation(self):
        # Test upload without selfie first
        data = {'id_card_image': self.test_image}
        serializer = IDCardUploadSerializer(
            instance=self.verification,
            data=data,
            context={'verification': self.verification},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        
        # Set status to selfie_uploaded and test again
        self.verification.status = 'selfie_uploaded'
        self.verification.save()
        
        serializer = IDCardUploadSerializer(
            instance=self.verification,
            data=data,
            context={'verification': self.verification},
            partial=True
        )
        self.assertTrue(serializer.is_valid())

    def test_id_card_upload_serializer_update(self):
        self.verification.status = 'selfie_uploaded'
        self.verification.save()
        
        data = {'id_card_image': self.test_image}
        serializer = IDCardUploadSerializer(
            instance=self.verification,
            data=data,
            context={'verification': self.verification},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_instance = serializer.save()
        self.assertIsNotNone(updated_instance.id_card_image)

    def test_selfie_with_id_serializer_validation(self):
        data = {'selfie_with_id_image': self.test_image}
        serializer = SelfieWithIDSerializer(
            instance=self.verification,
            data=data,
            context={'verification': self.verification},
            partial=True
        )
        self.assertFalse(serializer.is_valid())
        
        # Set status to id_uploaded and test again
        self.verification.status = 'id_uploaded'
        self.verification.save()
        
        serializer = SelfieWithIDSerializer(
            instance=self.verification,
            data=data,
            context={'verification': self.verification},
            partial=True
        )
        self.assertTrue(serializer.is_valid())

    def test_selfie_with_id_serializer_update(self):
        self.verification.status = 'id_uploaded'
        self.verification.save()
        
        data = {'selfie_with_id_image': self.test_image}
        serializer = SelfieWithIDSerializer(
            instance=self.verification,
            data=data,
            context={'verification': self.verification},
            partial=True
        )
        self.assertTrue(serializer.is_valid())
        updated_instance = serializer.save()
        self.assertIsNotNone(updated_instance.selfie_with_id_image)

    def test_verification_status_serializer(self):
        serializer = VerificationStatusSerializer(instance=self.verification)
        data = serializer.data
        
        self.assertIn('status', data)
        self.assertIn('created_at', data)
        self.assertIn('updated_at', data)

    def tearDown(self):
        if self.verification.selfie_image:
            self.verification.selfie_image.delete()
        if self.verification.id_card_image:
            self.verification.id_card_image.delete()
        if self.verification.selfie_with_id_image:
            self.verification.selfie_with_id_image.delete()


