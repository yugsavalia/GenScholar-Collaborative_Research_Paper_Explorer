import json
import os
from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.contrib.messages import get_messages
from django.http import HttpResponse
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from accounts.models import EmailOTP, PendingEmailVerification


@override_settings(
    EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
    EMAIL_HOST='smtp.gmail.com',
    EMAIL_HOST_USER='app@test.com',
    EMAIL_HOST_PASSWORD='pwd',
    EMAIL_PORT=587,
    EMAIL_USE_TLS=True,
    DEFAULT_FROM_EMAIL='noreply@test.com'
)
class AccountViewAdditionalTests(TestCase):
    """Targeted coverage for accounts.views error and edge flows (Logic & Mocking)."""

    def setUp(self):
        self.client = Client()
        self.existing_email = 'existing@test.com'
        User.objects.create_user(
            username='existing',
            email=self.existing_email,
            password='pass123'
        )

    def _collect_messages(self, response):
        return [str(msg) for msg in get_messages(response.wsgi_request)]

    @patch('accounts.views.render', return_value=HttpResponse(''))
    def test_request_email_verification_requires_email(self, _render):
        response = self.client.post(reverse('request_email_verification'), {'email': ''})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Email is required.', self._collect_messages(response))

    @patch('accounts.views.render', return_value=HttpResponse(''))
    def test_request_email_verification_invalid_email(self, _render):
        response = self.client.post(reverse('request_email_verification'), {'email': 'bad-value'})
        self.assertEqual(response.status_code, 200)
        self.assertIn('Invalid email address.', self._collect_messages(response))

    @patch('accounts.views.render', return_value=HttpResponse(''))
    def test_request_email_verification_existing_user(self, _render):
        response = self.client.post(
            reverse('request_email_verification'),
            {'email': self.existing_email}
        )
        self.assertEqual(response.status_code, 200)
        self.assertIn('An account with this email already exists.', self._collect_messages(response))

    @patch('accounts.views.render', return_value=HttpResponse(''))
    @patch('django.core.mail.get_connection')
    @patch('accounts.views.send_mail')
    def test_request_email_verification_success(self, mock_send, mock_connection, _render):
        mock_connection.return_value = MagicMock()
        mock_send.return_value = 1
        email = 'new@test.com'
        response = self.client.post(reverse('request_email_verification'), {'email': email})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PendingEmailVerification.objects.filter(email=email).exists())
        self.assertTrue(any('Verification link sent' in msg for msg in self._collect_messages(response)))
        mock_send.assert_called_once()

    @patch('accounts.views.render', return_value=HttpResponse(''))
    @patch('django.core.mail.get_connection')
    @patch('accounts.views.send_mail')
    def test_request_email_verification_email_failure(self, mock_send, mock_connection, _render):
        mock_connection.return_value = MagicMock()
        mock_send.side_effect = ValueError('Boom')
        response = self.client.post(reverse('request_email_verification'), {'email': 'split@test.com'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('Failed to send verification email' in msg for msg in self._collect_messages(response)))

    @patch.dict(os.environ, {'EMAIL_HOST_USER': 'env-user@gmail.com'})
    @override_settings(DEFAULT_FROM_EMAIL='', EMAIL_HOST_USER='env-user@gmail.com', EMAIL_HOST='smtp.gmail.com')
    @patch('accounts.views.render', return_value=HttpResponse(''))
    @patch('django.core.mail.get_connection')
    @patch('accounts.views.send_mail')
    def test_request_email_verification_from_email_fallback(self, mock_send, mock_connection, _render):
        mock_connection.return_value = MagicMock()
        mock_send.return_value = 1
        response = self.client.post(reverse('request_email_verification'), {'email': 'fallback@test.com'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(PendingEmailVerification.objects.filter(email='fallback@test.com').exists())

    @patch('accounts.views.render', return_value=HttpResponse(''))
    @patch('django.core.mail.get_connection')
    @patch('accounts.views.send_mail')
    def test_request_email_verification_connection_error_message(self, mock_send, mock_connection, _render):
        mock_connection.return_value = MagicMock()
        mock_send.side_effect = Exception('timeout reached')
        response = self.client.post(reverse('request_email_verification'), {'email': 'timeout@test.com'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(any('Could not connect to email server' in msg for msg in self._collect_messages(response)))

    def test_resend_verification_email_success(self):
        adapter = MagicMock()
        with patch('accounts.views.get_adapter', return_value=adapter):
            response = self.client.post(reverse('resend_verification'), {'email': self.existing_email})
        self.assertEqual(response.status_code, 302)
        self.assertIn('Verification email sent', self._collect_messages(response)[0])

    def test_resend_verification_email_user_not_found(self):
        adapter = MagicMock()
        with patch('accounts.views.get_adapter', return_value=adapter):
            response = self.client.post(reverse('resend_verification'), {'email': 'missing@test.com'})
        self.assertEqual(response.status_code, 302)
        self.assertIn('User not found', self._collect_messages(response)[0])

    def test_resend_verification_email_blank(self):
        response = self.client.post(reverse('resend_verification'), {})
        self.assertEqual(response.status_code, 302)
        self.assertIn('Email is required', self._collect_messages(response)[0])

    def test_verify_email_token_without_token(self):
        response = self.client.get(reverse('verify_email_token'))
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('request_email_verification'))

    def test_verify_email_token_invalid_token(self):
        response = self.client.get(f"{reverse('verify_email_token')}?token=bad")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('request_email_verification'))

    def test_verify_email_token_expired(self):
        token_email = 'expire@test.com'
        token = PendingEmailVerification.generate_token(token_email)
        pending = PendingEmailVerification.objects.create(email=token_email, token=token, created_at=timezone.now() - timedelta(days=2))
        response = self.client.get(f"{reverse('verify_email_token')}?token={token}")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(response.url, reverse('request_email_verification'))
        self.assertFalse(PendingEmailVerification.objects.filter(pk=pending.pk).exists())

    @patch('django.core.mail.get_connection')
    @patch('accounts.views.send_mail')
    def test_api_request_email_verification_success(self, mock_send, mock_connection):
        mock_connection.return_value = MagicMock()
        mock_send.return_value = 1
        payload = {'email': 'otp@test.com'}
        response = self.client.post(
            reverse('api_request_email_verification'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertTrue(EmailOTP.objects.filter(email=payload['email']).exists())

    def test_api_request_email_verification_missing_email(self):
        response = self.client.post(
            reverse('api_request_email_verification'),
            data=json.dumps({'email': ''}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Email is required', response.json()['message'])

    def test_api_request_email_verification_invalid_email(self):
        response = self.client.post(
            reverse('api_request_email_verification'),
            data=json.dumps({'email': 'missing-at'}),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Invalid email address', response.json()['message'])

    @patch('accounts.views.login')
    @patch('django.contrib.auth.password_validation.validate_password')
    @patch('allauth.account.models.EmailAddress')
    def test_api_signup_view_success(self, mock_emailaddress, mock_validate_password, mock_login):
        mock_validate_password.return_value = None
        does_not_exist = type('DoesNotExist', (Exception,), {})
        mock_emailaddress.DoesNotExist = does_not_exist
        mock_emailaddress.objects.get.side_effect = does_not_exist()
        mock_emailaddress.objects.create.return_value = MagicMock()
        otp = EmailOTP.objects.create(email='otp-success@test.com', otp='123456', is_verified=True)
        payload = {
            'username': 'coveruser',
            'email': otp.email,
            'password': 'ComplexPass!1',
            'confirm_password': 'ComplexPass!1'
        }
        response = self.client.post(
            reverse('api_signup'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 201)
        self.assertTrue(response.json()['success'])

    def test_api_signup_view_requires_otp(self):
        payload = {
            'username': 'unverified',
            'email': 'no-otp@test.com',
            'password': 'ComplexPass!1',
            'confirm_password': 'ComplexPass!1'
        }
        response = self.client.post(
            reverse('api_signup'),
            data=json.dumps(payload),
            content_type='application/json'
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn('Email verification required', response.json()['message'])


class AccountsViewsCoverageTestCase(TestCase):
    """Additional tests to cover missing lines in accounts/views.py (API & Edge Cases)."""

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
        EmailOTP.objects.create(email='new@example.com', otp='123456', is_verified=True)
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