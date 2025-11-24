from django.db import models
from django.utils import timezone
from django.core.signing import Signer
from django.utils import timezone as tz
from datetime import timedelta
import secrets
import random


class PendingEmailVerification(models.Model):
    """Model for storing pending email verifications before account creation."""
    email = models.EmailField(unique=True)
    token = models.CharField(max_length=255, unique=True)
    created_at = models.DateTimeField(default=timezone.now)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Pending verification for {self.email}"
    
    def is_expired(self):
        """Check if token is expired (24 hours)."""
        return timezone.now() > self.created_at + timedelta(hours=24)
    
    @classmethod
    def generate_token(cls, email):
        """Generate a signed token for email verification."""
        signer = Signer()
        token_data = f"{email}:{secrets.token_urlsafe(32)}"
        signed_token = signer.sign(token_data)
        return signed_token
    
    @classmethod
    def verify_token(cls, token):
        """Verify and extract email from token."""
        try:
            signer = Signer()
            unsigned_data = signer.unsign(token)
            email = unsigned_data.split(':')[0]
            return email
        except Exception:
            return None


class EmailOTP(models.Model):
    """Model for storing OTP verification codes."""
    email = models.EmailField(unique=True)
    otp = models.CharField(max_length=6)
    created_at = models.DateTimeField(default=timezone.now)
    is_verified = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-created_at']
    
    def __str__(self):
        return f"OTP for {self.email}"
    
    def is_expired(self):
        """Check if OTP is expired (10 minutes)."""
        return timezone.now() > self.created_at + timedelta(minutes=10)
    
    @classmethod
    def generate_otp(cls):
        """Generate a random 6-digit OTP."""
        return str(random.randint(100000, 999999))
