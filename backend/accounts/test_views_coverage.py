"""
Additional tests for accounts/views.py to increase coverage to 95%+.
"""
from django.test import TestCase, Client
from django.contrib.auth.models import User
import json


class AccountsViewsCoverageTestCase(TestCase):
    """Additional tests to cover missing lines in accounts/views.py."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_api_login_view_method_not_post(self):
        """Test api_login_view with non-POST method."""
        response = self.client.get('/api/auth/login/')
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_login_view_already_authenticated(self):
        """Test api_login_view when user is already authenticated."""
        self.client.force_login(self.user)
        response = self.client.post('/api/auth/login/', json.dumps({
            'identifier': 'testuser',
            'password': 'testpass123'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_login_view_exception(self):
        """Test api_login_view with exception."""
        # Test with invalid JSON
        response = self.client.post('/api/auth/login/', 'invalid json', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_signup_view_method_not_post(self):
        """Test api_signup_view with non-POST method."""
        response = self.client.get('/api/auth/signup/')
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_signup_view_already_authenticated(self):
        """Test api_signup_view when user is already authenticated."""
        self.client.force_login(self.user)
        response = self.client.post('/api/auth/signup/', json.dumps({
            'username': 'newuser',
            'email': 'new@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_signup_view_missing_username(self):
        """Test api_signup_view without username."""
        response = self.client.post('/api/auth/signup/', json.dumps({
            'email': 'test@example.com',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Username', data['message'])
    
    def test_api_signup_view_missing_email(self):
        """Test api_signup_view without email."""
        response = self.client.post('/api/auth/signup/', json.dumps({
            'username': 'newuser',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('Email', data['message'])
    
    def test_api_signup_view_invalid_email_regex(self):
        """Test api_signup_view with invalid email format (regex check)."""
        response = self.client.post('/api/auth/signup/', json.dumps({
            'username': 'newuser',
            'email': 'invalid-email',
            'password': 'testpass123',
            'confirm_password': 'testpass123'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
        self.assertIn('email', data['message'].lower())
    
    def test_api_signup_view_exception(self):
        """Test api_signup_view with exception."""
        response = self.client.post('/api/auth/signup/', 'invalid json', content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_logout_view_method_not_post(self):
        """Test api_logout_view with non-POST method."""
        response = self.client.get('/api/auth/logout/')
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_get_user_view_method_not_get(self):
        """Test api_get_user_view with non-GET method."""
        response = self.client.post('/api/auth/user/')
        self.assertEqual(response.status_code, 405)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_login_view_general_exception(self):
        """Test api_login_view with general exception."""
        # Mock authenticate to raise an exception
        from unittest.mock import patch
        with patch('accounts.views.authenticate', side_effect=Exception("Test exception")):
            response = self.client.post('/api/auth/login/', json.dumps({
                'identifier': 'testuser',
                'password': 'testpass123'
            }), content_type='application/json')
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertFalse(data['success'])
    
    def test_api_signup_view_email_regex_fails(self):
        """Test api_signup_view when email regex validation fails."""
        # Use an email that passes validate_email but fails regex
        response = self.client.post('/api/auth/signup/', json.dumps({
            'username': 'newuser',
            'email': 'test@',  # Invalid format
            'password': 'ComplexPass123!',
            'confirm_password': 'ComplexPass123!'
        }), content_type='application/json')
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_signup_view_general_exception(self):
        """Test api_signup_view with general exception."""
        from unittest.mock import patch
        with patch('accounts.views.User.objects.create_user', side_effect=Exception("Test exception")):
            response = self.client.post('/api/auth/signup/', json.dumps({
                'username': 'newuser',
                'email': 'new@example.com',
                'password': 'ComplexPass123!',
                'confirm_password': 'ComplexPass123!'
            }), content_type='application/json')
            self.assertEqual(response.status_code, 500)
            data = json.loads(response.content)
            self.assertFalse(data['success'])

