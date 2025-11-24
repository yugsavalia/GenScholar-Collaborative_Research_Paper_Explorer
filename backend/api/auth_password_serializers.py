"""
Password reset serializers for DRF
"""
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.core.exceptions import ValidationError


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request (forgot password)."""
    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        """Normalize email to lowercase."""
        return value.lower().strip()


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""
    uid = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})
    re_new_password = serializers.CharField(required=True, write_only=True, style={'input_type': 'password'})

    def validate(self, attrs):
        """Validate that passwords match and meet Django's validators."""
        new_password = attrs.get('new_password')
        re_new_password = attrs.get('re_new_password')

        if new_password != re_new_password:
            raise serializers.ValidationError({
                're_new_password': 'Passwords do not match.'
            })

        # Validate password using Django's validators
        try:
            validate_password(new_password)
        except ValidationError as e:
            raise serializers.ValidationError({
                'new_password': list(e.messages)
            })

        return attrs

