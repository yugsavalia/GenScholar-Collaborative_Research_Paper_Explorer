
from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse
import json
from accounts.auth_backends import UsernameOrEmailBackend
from accounts.models import EmailOTP
from accounts.views import (
    signup_view, login_view, api_csrf_view,
    api_login_view, api_signup_view, api_logout_view, api_get_user_view
)


class AccountsModelTestCase(TestCase):
    """Test account-related models (User model from Django)."""
    
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_user_creation(self):
        """Test that a user can be created."""
        self.assertIsNotNone(self.user.id)
        self.assertEqual(self.user.username, 'testuser')
        self.assertEqual(self.user.email, 'test@example.com')
    
    def test_user_str(self):
        """Test user string representation."""
        self.assertEqual(str(self.user), 'testuser')


class AccountsViewsTestCase(TestCase):
    """Test account views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_signup_view_get(self):
        """Test signup view GET request redirects to email verification when not authenticated."""
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 302)
    
    def test_signup_view_post_valid(self):
        """Test signup view POST with valid data."""
        response = self.client.post(reverse('signup'), {
            'username': 'newuser',
            'password1': 'complexpass123',
            'password2': 'complexpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after signup
        self.assertFalse(User.objects.filter(username='newuser').exists())
    
    def test_signup_view_redirects_authenticated(self):
        """Test that authenticated users are redirected from signup."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('signup'))
        self.assertEqual(response.status_code, 302)
    
    def test_login_view_get(self):
        """Test login view GET request."""
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
    
    def test_login_view_post_valid(self):
        """Test login view POST with valid credentials."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'testpass123'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after login
    
    def test_login_view_post_invalid(self):
        """Test login view POST with invalid credentials."""
        response = self.client.post(reverse('login'), {
            'username': 'testuser',
            'password': 'wrongpass'
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('error', response.context)
    
    def test_login_view_redirects_authenticated(self):
        """Test that authenticated users are redirected from login."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 302)


class AccountsAPIViewsTestCase(TestCase):
    """Test account API views."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_api_csrf_view_get(self):
        """Test CSRF token API endpoint."""
        response = self.client.get('/api/auth/csrf/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertIn('csrf_token', data['data'])
    
    def test_api_csrf_view_post_not_allowed(self):
        """Test CSRF token API endpoint doesn't allow POST."""
        response = self.client.post('/api/auth/csrf/')
        self.assertEqual(response.status_code, 405)
    
    def test_api_login_view_post_valid_username(self):
        """Test API login with username."""
        response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({
                'identifier': 'testuser',
                'password': 'testpass123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['user']['username'], 'testuser')
    
    def test_api_login_view_post_valid_email(self):
        """Test API login with email."""
        response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({
                'identifier': 'test@example.com',
                'password': 'testpass123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_login_view_post_invalid_credentials(self):
        """Test API login with invalid credentials."""
        response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({
                'identifier': 'testuser',
                'password': 'wrongpass'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_login_view_post_missing_fields(self):
        """Test API login with missing fields."""
        response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({
                'identifier': 'testuser'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
    
    def test_api_login_view_already_authenticated(self):
        """Test API login when already authenticated."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post(
            '/api/auth/login/',
            data=json.dumps({
                'identifier': 'testuser',
                'password': 'testpass123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_signup_view_post_valid(self):
        """Test API signup with valid data."""
        EmailOTP.objects.create(email='newuser@example.com', otp='123456', is_verified=True)
        response = self.client.post(
            '/api/auth/signup/',
            data=json.dumps({
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'complexpass123',
                'confirm_password': 'complexpass123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertTrue(User.objects.filter(username='newuser').exists())
    
    def test_api_signup_view_post_passwords_dont_match(self):
        """Test API signup with mismatched passwords."""
        response = self.client.post(
            '/api/auth/signup/',
            data=json.dumps({
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': 'complexpass123',
                'confirm_password': 'differentpass'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_signup_view_post_invalid_email(self):
        """Test API signup with invalid email."""
        response = self.client.post(
            '/api/auth/signup/',
            data=json.dumps({
                'username': 'newuser',
                'email': 'invalid-email',
                'password': 'complexpass123',
                'confirm_password': 'complexpass123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_signup_view_post_duplicate_username(self):
        """Test API signup with duplicate username."""
        response = self.client.post(
            '/api/auth/signup/',
            data=json.dumps({
                'username': 'testuser',  # Already exists
                'email': 'newemail@example.com',
                'password': 'complexpass123',
                'confirm_password': 'complexpass123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_signup_view_post_duplicate_email(self):
        """Test API signup with duplicate email."""
        response = self.client.post(
            '/api/auth/signup/',
            data=json.dumps({
                'username': 'newuser',
                'email': 'test@example.com',  # Already exists
                'password': 'complexpass123',
                'confirm_password': 'complexpass123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_logout_view_post_authenticated(self):
        """Test API logout when authenticated."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_logout_view_post_unauthenticated(self):
        """Test API logout when not authenticated."""
        response = self.client.post('/api/auth/logout/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
    
    def test_api_get_user_view_get_authenticated(self):
        """Test API get user when authenticated."""
        self.client.login(username='testuser', password='testpass123')
        response = self.client.get('/api/auth/user/')
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertTrue(data['success'])
        self.assertEqual(data['data']['user']['username'], 'testuser')
    
    def test_api_get_user_view_get_unauthenticated(self):
        """Test API get user when not authenticated."""
        response = self.client.get('/api/auth/user/')
        self.assertEqual(response.status_code, 401)
        data = json.loads(response.content)
        self.assertFalse(data['success'])


class UsernameOrEmailBackendTestCase(TestCase):
    """Test custom authentication backend."""
    
    def setUp(self):
        self.backend = UsernameOrEmailBackend()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
    
    def test_authenticate_with_username(self):
        """Test authentication with username."""
        user = self.backend.authenticate(
            request=None,
            username='testuser',
            password='testpass123'
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
    
    def test_authenticate_with_email(self):
        """Test authentication with email."""
        user = self.backend.authenticate(
            request=None,
            username='test@example.com',
            password='testpass123'
        )
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
    
    def test_authenticate_with_wrong_password(self):
        """Test authentication with wrong password."""
        user = self.backend.authenticate(
            request=None,
            username='testuser',
            password='wrongpass'
        )
        self.assertIsNone(user)
    
    def test_authenticate_with_nonexistent_user(self):
        """Test authentication with nonexistent user."""
        user = self.backend.authenticate(
            request=None,
            username='nonexistent',
            password='testpass123'
        )
        self.assertIsNone(user)
    
    def test_authenticate_with_missing_credentials(self):
        """Test authentication with missing credentials."""
        user = self.backend.authenticate(
            request=None,
            username=None,
            password='testpass123'
        )
        self.assertIsNone(user)
    
    def test_get_user(self):
        """Test get_user method."""
        user = self.backend.get_user(self.user.id)
        self.assertIsNotNone(user)
        self.assertEqual(user.username, 'testuser')
    
    def test_get_user_nonexistent(self):
        """Test get_user with nonexistent ID."""
        user = self.backend.get_user(99999)
        self.assertIsNone(user)
    
    def test_api_login_view_exception_handling(self):
        """Test API login view exception handling."""
        # Test with invalid JSON
        response = self.client.post(
            '/api/auth/login/',
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_signup_view_weak_password(self):
        """Test API signup with weak password."""
        response = self.client.post(
            '/api/auth/signup/',
            data=json.dumps({
                'username': 'newuser',
                'email': 'newuser@example.com',
                'password': '123',  # Too short
                'confirm_password': '123'
            }),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
    
    def test_api_signup_view_exception_handling(self):
        """Test API signup view exception handling."""
        # Test with invalid JSON
        response = self.client.post(
            '/api/auth/signup/',
            data='invalid json',
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertFalse(data['success'])
