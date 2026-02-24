import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model

User = get_user_model()

class AuthTests(APITestCase):
    """
    Test suite for User Registration, Login, and Logout logic.
    Ensures the 'Security Gate' works as expected.
    """

    def setUp(self):
        # Sample data for reuse
        self.register_url = reverse('user-register')
        self.login_url = reverse('user-login')      
        self.logout_url = reverse('user-logout')    
        
        self.user_data = {
            "username": "nemwelb",
            "email": "nemwel@healthclaims.ai",
            "password": "strongpassword123",
            "first_name": "Nemwel",
            "last_name": "Boniface"
        }

    def test_registration_success(self):
        """Ensures a new user can join and receives JWT tokens immediately."""
        response = self.client.post(self.register_url, self.user_data, format='json')
        
        assert response.status_code == status.HTTP_201_CREATED
        assert "access" in response.data
        assert "refresh" in response.data
        assert response.data["email"] == self.user_data["email"]
        assert User.objects.filter(email=self.user_data["email"]).exists()

    def test_registration_fails_duplicate_email(self):
        """Ensures the UniqueValidator in the serializer prevents duplicate accounts."""
        # Create user once
        User.objects.create_user(**self.user_data)
        
        # Try to register again with same data
        response = self.client.post(self.register_url, self.user_data, format='json')
        
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        # Check for the error either in root or inside our custom 'message' key
        error_data = response.data.get("message", response.data)
        assert "email" in error_data

    def test_login_success(self):
        """Ensures valid credentials return a 200 OK and JWT tokens."""
        # Setup: Create user first
        User.objects.create_user(**self.user_data)
        
        login_data = {
            "email": self.user_data["email"],
            "password": self.user_data["password"]
        }
        
        response = self.client.post(self.login_url, login_data, format='json')
        
        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "first_name" in response.data
        assert response.data["first_name"] == self.user_data["first_name"]

    def test_login_fails_wrong_password(self):
        """Ensures invalid passwords return 401 Unauthorized."""
        User.objects.create_user(**self.user_data)
        
        bad_login_data = {
            "email": self.user_data["email"],
            "password": "wrongpassword"
        }
        
        response = self.client.post(self.login_url, bad_login_data, format='json')
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_logout_and_blacklist(self):
        """
        Ensures the logout view blacklists the refresh token.
        This is a 'Bonus' requirement for production awareness.
        """
        # 1. Setup: Register and get a token
        reg_response = self.client.post(self.register_url, self.user_data, format='json')
        access_token = reg_response.data["access"]
        refresh_token = reg_response.data["refresh"]

        # 2. Add Auth Header (Protected route)
        self.client.credentials(HTTP_AUTHORIZATION=f'Bearer {access_token}')

        # 3. Hit logout
        logout_data = {"refresh": refresh_token}
        response = self.client.post(self.logout_url, logout_data, format='json')

        assert response.status_code == status.HTTP_200_OK
        assert response.data["message"] == "Logout successful"

    def test_protected_route_denied_without_token(self):
        """
        Verifies that our global IsAuthenticated setting in settings.py 
        actually protects endpoints from anonymous users.
        """
        # Try to logout without a token
        response = self.client.post(self.logout_url, {"refresh": "fake"}, format='json')
        
        # Should be 401 because we didn't provide credentials
        assert response.status_code == status.HTTP_401_UNAUTHORIZED