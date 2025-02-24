from django.db import models
from django.conf import settings
from cryptography.fernet import Fernet
import base64
from django.contrib.auth import get_user_model

User = get_user_model()

class UserVerification(models.Model):
    VERIFICATION_STATES = (
        ('pending', 'Pending'),
        ('selfie_uploaded', 'Selfie Uploaded'),
        ('id_uploaded', 'ID Uploaded'),
        ('selfie_with_id_uploaded', 'Selfie With ID Uploaded'),
        ('verified', 'Verified'),
        ('rejected', 'Rejected'),
    )

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='verification'
    )
    selfie_image = models.ImageField(
        upload_to='verification/selfies/',
        null=True,
        blank=True
    )
    id_card_image = models.ImageField(
        upload_to='verification/id_cards/',
        null=True,
        blank=True
    )
    selfie_with_id_image = models.ImageField(
        upload_to='verification/selfie_with_id/',
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=24,
        choices=VERIFICATION_STATES,
        default='pending'
    )
    encryption_key = models.BinaryField(null=True, blank=True)  # Store Fernet key
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Verification for {self.user.email}"

    def generate_encryption_key(self):
        """Generate and store a Fernet key if not already present."""
        if not self.encryption_key:
            key = Fernet.generate_key()
            self.encryption_key = key
            self.save()
        return Fernet(self.encryption_key)

    def encrypt_image(self, image_file):
        """Encrypt the image file content."""
        fernet = self.generate_encryption_key()
        image_content = image_file.read()
        encrypted_content = fernet.encrypt(image_content)
        image_file.seek(0)  # Reset file pointer
        image_file.write(encrypted_content)
        image_file.truncate()  # Ensure file size matches encrypted content
        return image_file

    def decrypt_image(self, image_field):
        """Decrypt the image content from the specified field."""
        if not image_field or not self.encryption_key:
            return None
        fernet = Fernet(self.encryption_key)
        with image_field.open('rb') as f:
            encrypted_content = f.read()
        return fernet.decrypt(encrypted_content)
