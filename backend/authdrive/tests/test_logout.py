from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

User = get_user_model()

class LogoutViewTest(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@logout.com',
            password='testpass123',
            is_active=True
        )

        # Set up API client
        self.client = APIClient()

        # Generate JWT tokens
        refresh = RefreshToken.for_user(self.user)
        self.access_token = str(refresh.access_token)
        self.refresh_token = str(refresh)

        # Set JWT credentials
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {self.access_token}')

    def test_logout_success(self):
        """Test successful logout with valid refresh token."""
        url = reverse('logout')
        data = {'refresh': self.refresh_token}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)
        self.assertEqual(response.data['message'], 'Logout successful. Tokens invalidated.')

        # Verify refresh token is blacklisted
        self.assertTrue(BlacklistedToken.objects.filter(token__token=self.refresh_token).exists())

    def test_logout_missing_refresh_token(self):
        """Test logout with missing refresh token."""
        url = reverse('logout')
        response = self.client.post(url, {})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertEqual(response.data['detail'], 'Refresh token is required.')

    def test_logout_invalid_refresh_token(self):
        """Test logout with invalid refresh token."""
        url = reverse('logout')
        data = {'refresh': 'invalid_refresh_token'}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('detail', response.data)

    def test_logout_unauthenticated(self):
        """Test logout without JWT authentication."""
        url = reverse('logout')
        self.client.credentials()  # Clear JWT credentials
        data = {'refresh': self.refresh_token}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_blacklisted_refresh_token_cannot_be_used(self):
        """Test that a blacklisted refresh token cannot be used to refresh access token."""
        # Blacklist the refresh token
        url = reverse('logout')
        data = {'refresh': self.refresh_token}
        self.client.post(url, data)

        # Try to refresh access token with blacklisted refresh token
        refresh_url = reverse('token_refresh')
        response = self.client.post(refresh_url, {'refresh': self.refresh_token})

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Token is blacklisted')
