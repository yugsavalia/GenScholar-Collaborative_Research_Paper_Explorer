"""
Tests for django-allauth integration: email verification on signup.
"""
from django.test import TestCase, Client, override_settings
from django.contrib.auth.models import User
from django.core import mail
from allauth.account.models import EmailAddress


class EmailVerificationTest(TestCase):
    """Test that signup triggers email verification."""
    
    def setUp(self):
        """Set up test client."""
        self.client = Client()
    
    @override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend')
    def test_signup_sends_verification_email(self):
        """Test that creating a user via signup sends a verification email."""
        # Clear mail outbox
        mail.outbox = []
        
        # Sign up a new user
        response = self.client.post('/accounts/signup/', {
            'username': 'testuser',
            'email': 'test@example.com',
            'email2': 'test@example.com',  # allauth requires email confirmation
            'password1': 'TestPassword123!',
            'password2': 'TestPassword123!',
        })
        
        # Check that signup was successful (redirect or 200 with success message)
        self.assertIn(response.status_code, [200, 302])
        
        # Check that user was created
        user = User.objects.get(username='testuser')
        self.assertIsNotNone(user)
        
        # Check that an email was sent
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn('verification', mail.outbox[0].subject.lower())
        self.assertIn('test@example.com', mail.outbox[0].to)
        
        # Check that EmailAddress record exists but is not verified
        email_address = EmailAddress.objects.get(email='test@example.com')
        self.assertFalse(email_address.verified)
        self.assertEqual(email_address.user, user)
    
    def test_email_verification_required_before_login(self):
        """Test that unverified users cannot log in."""
        # Create user with unverified email
        user = User.objects.create_user(
            username='unverified',
            email='unverified@example.com',
            password='TestPassword123!'
        )
        EmailAddress.objects.create(
            user=user,
            email='unverified@example.com',
            verified=False
        )
        
        # Try to login
        response = self.client.post('/accounts/login/', {
            'login': 'unverified',
            'password': 'TestPassword123!',
        })
        
        # Should not redirect to dashboard (email not verified)
        # allauth will show an error or redirect to email verification page
        self.assertNotEqual(response.status_code, 302)  # Not a successful redirect

