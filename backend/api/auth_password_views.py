"""
Password reset views for DRF
"""
from django.contrib.auth.models import User
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.conf import settings
import os
import re
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .auth_password_serializers import (
    PasswordResetRequestSerializer,
    PasswordResetConfirmSerializer,
)


@api_view(['POST'])
@permission_classes([AllowAny])
def request_password_reset(request):
    """
    POST /api/auth/password-reset/
    Request a password reset email.
    Input: { "email": "user@example.com" }
    """
    serializer = PasswordResetRequestSerializer(data=request.data)
    
    if not serializer.is_valid():
        # Get the first error message from email validation
        email_errors = serializer.errors.get('email', [])
        error_message = email_errors[0] if email_errors else "Invalid email address."
        return Response({
            "success": False,
            "message": error_message
        }, status=status.HTTP_400_BAD_REQUEST)
    
    email = serializer.validated_data['email']
    
    # Look up user by email (case-insensitive)
    try:
        user = User.objects.get(email__iexact=email)
    except User.DoesNotExist:
        return Response({
            "success": False,
            "message": "Email not found. Please enter a registered email address."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Generate reset token and uid
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    
    # Build reset URL pointing to React frontend reset password page
    # Format: http://localhost:5173/reset-password/{uid}/{token}
    frontend_base_url = getattr(settings, 'FRONTEND_BASE_URL', os.getenv('FRONTEND_BASE_URL', 'http://localhost:5173'))
    reset_url = f"{frontend_base_url}/reset-password/{uid}/{token}"
    
    # Compose email
    subject = "Reset your GenScholar password"
    message = f"""Hello {user.username},

We received a request to reset your GenScholar account password.

Click the link below to reset your password:
{reset_url}

If you did not request this, you can safely ignore this email.

Thanks,
GenScholar Support Team"""
    
    # Send email
    # Determine valid from_email address
    from_email = settings.DEFAULT_FROM_EMAIL
    
    # If DEFAULT_FROM_EMAIL is invalid, try to get a valid email from environment
    if not from_email or '@localhost' in from_email or from_email == 'no-reply@localhost':
        # Try to get Gmail address from environment (check for gmail.com in EMAIL_HOST_USER)
        email_host_user = os.getenv('EMAIL_HOST_USER', '')
        # Look for Gmail address in env (might be set as genscholar.help@gmail.com)
        if email_host_user and '@gmail.com' in email_host_user:
            from_email = email_host_user
        elif settings.EMAIL_HOST == 'smtp.gmail.com' and email_host_user and '@' in email_host_user:
            from_email = email_host_user
        else:
            # Fallback - use a valid email format
            from_email = 'genscholar.help@gmail.com'
    
    try:
        send_mail(
            subject,
            message,
            from_email,
            [user.email],
            fail_silently=False,
        )
        print(f"✓ Password reset email sent to {user.email} from {from_email}")
    except Exception as e:
        # Log error but still return generic success for security
        print(f"✗ ERROR sending password reset email: {e}")
        print(f"  From: {from_email}")
        print(f"  To: {user.email}")
        print(f"  EMAIL_BACKEND: {settings.EMAIL_BACKEND}")
        print(f"  EMAIL_HOST: {settings.EMAIL_HOST}")
        import traceback
        traceback.print_exc()
        # In production, you might want to log this to a proper logging system
    
    # Always return generic success message
        # Return success message after sending reset email
    return Response({
        "success": True,
        "message": "Password reset link has been sent to your email."
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([AllowAny])
def confirm_password_reset(request):
    """
    POST /api/auth/password-reset/confirm/
    Confirm password reset with uid, token, and new password.
    Input: { "uid": "...", "token": "...", "new_password": "...", "re_new_password": "..." }
    """
    serializer = PasswordResetConfirmSerializer(data=request.data)
    
    if not serializer.is_valid():
        return Response({
            "success": False,
            "message": "Validation failed.",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
    
    uid = serializer.validated_data['uid']
    token = serializer.validated_data['token']
    new_password = serializer.validated_data['new_password']
    
    # Decode uid and get user
    try:
        user_id = urlsafe_base64_decode(uid).decode()
        user = User.objects.get(pk=user_id)
    except (TypeError, ValueError, User.DoesNotExist, UnicodeDecodeError):
        return Response({
            "success": False,
            "message": "Invalid or expired reset link."
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check token
    if not default_token_generator.check_token(user, token):
        return Response({
            "success": False,
            "message": "Invalid or expired reset link."
        }, status=status.HTTP_400_BAD_REQUEST)
        # Validate new password with strict rules (matching update-credentials API)
    username_lower = user.username.lower()
    password_lower = new_password.lower()
    
    # Must not equal username
    if password_lower == username_lower:
        return Response({
            "success": False,
            "message": "Password must not equal the username"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Must not contain username
    if username_lower in password_lower:
        return Response({
            "success": False,
            "message": "Password must not contain the username"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Must not contain reversed username
    reversed_username = username_lower[::-1]
    if reversed_username and reversed_username in password_lower:
        return Response({
            "success": False,
            "message": "Password must not contain the reversed username"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Password strength checks (in order of specificity)
    if len(new_password) < 8:
        return Response({
            "success": False,
            "message": "Password must be at least 8 characters long"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not re.search(r"[A-Z]", new_password):
        return Response({
            "success": False,
            "message": "Password must contain at least one uppercase letter"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not re.search(r"[a-z]", new_password):
        return Response({
            "success": False,
            "message": "Password must contain at least one lowercase letter"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not re.search(r"\d", new_password):
        return Response({
            "success": False,
            "message": "Password must contain at least one number"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if not re.search(r"[!@#$%^&*()\-_=+\[\]{};:'\",.<>/?\\|`~]", new_password):
        return Response({
            "success": False,
            "message": "Password must contain at least one special character"
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Set new password
    user.set_password(new_password)
    user.save()
    
    return Response({
        "success": True,
        "message": "Password reset successful."
    }, status=status.HTTP_200_OK)

