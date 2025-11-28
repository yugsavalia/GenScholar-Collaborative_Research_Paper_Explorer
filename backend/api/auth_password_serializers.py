"""
Password reset serializers for DRF
"""
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.core.exceptions import ValidationError


class PasswordResetRequestSerializer(serializers.Serializer):
    """Serializer for password reset request (forgot password)."""
    email = serializers.CharField(required=True)
    
    def validate_email(self, value):
        """Normalize and strictly validate email format."""
        if not value:
            raise serializers.ValidationError("Email is required.")
        
        email = value.strip().lower()
        
        # Check if email is empty after stripping
        if not email:
            raise serializers.ValidationError("Email cannot be empty.")
        
        # Strict email validation: must have characters before and after '@'
        if '@' not in email:
            raise serializers.ValidationError("Invalid email format. Email must contain '@' symbol.")
        
        parts = email.split('@')
        if len(parts) != 2:
            raise serializers.ValidationError("Invalid email format. Email must contain exactly one '@' symbol.")
        
        local_part, domain = parts[0], parts[1]
        
        # Check local part (before @)
        if not local_part:
            raise serializers.ValidationError("Invalid email format. Email must have characters before '@' symbol.")
        
        # Check domain part (after @)
        if not domain:
            raise serializers.ValidationError("Invalid email format. Email must have characters after '@' symbol.")
        
        # Check for valid domain extension (must have at least one dot)
        if '.' not in domain:
            raise serializers.ValidationError("Invalid email format. Email must contain a valid domain extension (e.g., .com, .org).")
        
        domain_parts = domain.split('.')
        if len(domain_parts) < 2:
            raise serializers.ValidationError("Invalid email format. Email must contain a valid domain extension (e.g., .com, .org).")
        
                # Get TLD (last part after last dot)
        tld = domain_parts[-1]
        
        # TLD must be exactly 2-3 letters only
        if len(tld) < 2:
            raise serializers.ValidationError("Invalid email format. Domain extension must be at least 2 characters (e.g., .com, .in).")
        
        if len(tld) > 3:
            raise serializers.ValidationError("Invalid email format. Domain extension must be 2-3 characters only (e.g., .com, .in, .org).")
        
        # TLD must contain only letters (no numbers or special characters)
        if not tld.isalpha():
            raise serializers.ValidationError("Invalid email format. Domain extension must contain only letters (e.g., .com, .org).")
        
        # List of common valid TLDs
        valid_tlds = {
            # Common gTLDs
            'com', 'org', 'net', 'edu', 'gov', 'mil',
            # Country codes (common ones)
            'in', 'uk', 'us', 'ca', 'au', 'de', 'fr', 'it', 'es', 'nl', 'be', 'ch', 'at', 'se', 'no', 'dk', 'fi', 'pl', 'cz', 'ie', 'pt', 'gr', 'ro', 'hu', 'bg', 'hr', 'sk', 'si', 'lt', 'lv', 'ee', 'lu', 'mt', 'cy',
            'jp', 'cn', 'kr', 'tw', 'hk', 'sg', 'my', 'th', 'id', 'ph', 'vn', 'nz', 'za', 'eg', 'ma', 'ng', 'ke', 'tz', 'gh', 'et', 'ug', 'zm', 'zw', 'mw', 'mz', 'ao', 'bw', 'na', 'sz', 'ls', 'mg', 'mu', 'sc', 'km', 'dj', 'so', 'er', 'sd', 'ly', 'tn', 'dz', 'mr', 'ml', 'ne', 'td', 'cf', 'cm', 'gq', 'ga', 'cg', 'cd', 'bi', 'rw', 'ss', 'bf', 'ci', 'sn', 'gm', 'gn', 'gw', 'sl', 'lr', 'tg', 'bj', 'cv',
            'mx', 'br', 'ar', 'cl', 'co', 'pe', 've', 'ec', 'uy', 'py', 'bo', 'cr', 'pa', 'ni', 'hn', 'sv', 'gt', 'bz', 'do', 'cu', 'jm', 'tt', 'bb', 'gd', 'lc', 'vc', 'ag', 'bs', 'dm', 'ht', 'pr', 'vi',
            'ru', 'ua', 'by', 'kz', 'ge', 'am', 'az', 'tm', 'tj', 'kg', 'uz', 'mn', 'af', 'pk', 'bd', 'lk', 'np', 'bt', 'mv', 'mm', 'la', 'kh', 'bn',
            'il', 'jo', 'lb', 'sy', 'iq', 'ir', 'sa', 'ae', 'om', 'ye', 'kw', 'qa', 'bh', 'tr', 'cy',
            # Other common TLDs
            'io', 'co', 'me', 'tv', 'cc', 'ws', 'info', 'biz', 'name', 'pro', 'mobi', 'tel', 'asia', 'jobs', 'travel', 'xxx', 'aero', 'museum', 'coop', 'int'
        }
        
        # Validate TLD is in the list of valid extensions
        if tld not in valid_tlds:
            raise serializers.ValidationError("Invalid email format. Email must contain a valid domain extension such as .com, .in, .org, .net.")
        # TLD must contain only letters (no numbers or special characters)
        if not tld.isalpha():
            raise serializers.ValidationError("Invalid email format. Domain extension must contain only letters (e.g., .com, .org).")
        
        # Additional regex validation for comprehensive format check
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,3}$'
        if not re.match(email_pattern, email):
            raise serializers.ValidationError("Invalid email format. Please enter a valid email address.")
        
        return email


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

