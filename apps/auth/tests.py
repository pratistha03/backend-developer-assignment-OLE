"""
Tests for authentication and user management
"""
from django.test import TestCase
from django.contrib.auth import get_user_model
from rest_framework.test import APITestCase
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken

from apps.auth.models import Role

User = get_user_model()


class UserRegistrationTestCase(APITestCase):
    """Test user registration"""
    
    def test_user_registration_success(self):
        """Users should be able to register"""
        response = self.client.post('/api/user/register/', {
            'email': 'newuser@test.com',
            'full_name': 'New User',
            'role': Role.STUDENT,
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(User.objects.filter(email='newuser@test.com').exists())
        
        user = User.objects.get(email='newuser@test.com')
        self.assertEqual(user.role, Role.STUDENT)
        self.assertTrue(user.check_password('testpass123'))
    
    def test_registration_password_mismatch(self):
        """Registration should fail if passwords don't match"""
        response = self.client.post('/api/user/register/', {
            'email': 'newuser@test.com',
            'full_name': 'New User',
            'role': Role.STUDENT,
            'password': 'testpass123',
            'password_confirm': 'differentpass'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(email='newuser@test.com').exists())
    
    def test_registration_duplicate_email(self):
        """Registration should fail with duplicate email"""
        User.objects.create_user(
            email='existing@test.com',
            password='testpass123',
            full_name='Existing User',
            role=Role.STUDENT
        )
        
        response = self.client.post('/api/user/register/', {
            'email': 'existing@test.com',
            'full_name': 'New User',
            'role': Role.STUDENT,
            'password': 'testpass123',
            'password_confirm': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)


class AuthenticationTestCase(APITestCase):
    """Test authentication"""
    
    def setUp(self):
        """Set up test data"""
        self.user = User.objects.create_user(
            email='testuser@test.com',
            password='testpass123',
            full_name='Test User',
            role=Role.STUDENT
        )
    
    def test_login_success(self):
        """Users should be able to login with correct credentials"""
        response = self.client.post('/api/auth/login/', {
            'email': 'testuser@test.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)
        self.assertIn('authorities', response.data)
        self.assertEqual(response.data['authorities'], [Role.STUDENT])
        self.assertEqual(response.data['email'], 'testuser@test.com')
        self.assertEqual(response.data['full_name'], 'Test User')
        self.assertEqual(response.data['role'], Role.STUDENT)
    
    def test_login_invalid_credentials(self):
        """Login should fail with invalid credentials"""
        response = self.client.post('/api/auth/login/', {
            'email': 'testuser@test.com',
            'password': 'wrongpassword'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_login_nonexistent_user(self):
        """Login should fail for nonexistent user"""
        response = self.client.post('/api/auth/login/', {
            'email': 'nonexistent@test.com',
            'password': 'testpass123'
        })
        
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_token_refresh(self):
        """Users should be able to refresh tokens"""
        refresh_token = RefreshToken.for_user(self.user)
        
        response = self.client.post('/api/token/refresh/', {
            'refresh': str(refresh_token)
        })
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

