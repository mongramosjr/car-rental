from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.urls import reverse
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken

User = get_user_model()

class TokenEndpointTest(APITestCase):
    def setUp(self):
        # Create a test user
        self.user = User.objects.create_user(
            email='testuser@token.com',
            password='testpass123',
            is_active=True
        )

        # Set up API client
        self.client = APIClient()

    def test_obtain_token_pair_success(self):
        """Test obtaining access and refresh tokens with valid credentials."""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'testuser@token.com',
            'password': 'testpass123'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

        # Verify access token
        access_token = response.data['access']
        self.assertTrue(len(access_token) > 0)

        # Verify refresh token
        refresh_token = response.data['refresh']
        self.assertTrue(len(refresh_token) > 0)

    def test_obtain_token_pair_invalid_credentials(self):
        """Test obtaining tokens with invalid credentials."""
        url = reverse('token_obtain_pair')
        data = {
            'email': 'testuser@token.com',
            'password': 'wrongpassword'
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'No active account found with the given credentials')

    def test_obtain_token_pair_missing_fields(self):
        """Test obtaining tokens with missing email or password."""
        url = reverse('token_obtain_pair')
        
        # Missing password
        data = {'email': 'testuser@token.com'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

        # Missing email
        data = {'password': 'testpass123'}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('email', response.data)

    def test_refresh_token_success(self):
        """Test refreshing access token with valid refresh token."""
        # Obtain refresh token
        refresh = RefreshToken.for_user(self.user)
        refresh_token = str(refresh)

        url = reverse('token_refresh')
        data = {'refresh': refresh_token}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertTrue(len(response.data['access']) > 0)

    def test_refresh_token_invalid(self):
        """Test refreshing access token with invalid refresh token."""
        url = reverse('token_refresh')
        data = {'refresh': 'invalid_refresh_token'}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('detail', response.data)
        self.assertEqual(response.data['detail'], 'Token is invalid or expired')

    def test_refresh_token_missing(self):
        """Test refreshing access token with missing refresh token."""
        url = reverse('token_refresh')
        data = {}
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('refresh', response.data)
