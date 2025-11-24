"""
Custom authentication backend that allows users to login with either username OR email.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.db.models import Q

User = get_user_model()


class UsernameOrEmailBackend(ModelBackend):
    """
    Authenticate using either username or email (case-insensitive).
    
    This backend allows users to login with either their username or email address.
    It uses Django's default password validation.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate a user using username or email.
        
        Args:
            request: The HTTP request object
            username: Can be either username or email
            password: User's password
            **kwargs: Additional keyword arguments
            
        Returns:
            User object if authentication succeeds, None otherwise
        """
        if username is None or password is None:
            return None
        
        try:
            # Try to find user by username (case-insensitive) or email (case-insensitive)
            user = User.objects.get(
                Q(username__iexact=username) | Q(email__iexact=username)
            )
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a non-existing user
            User().set_password(password)
            return None
        except User.MultipleObjectsReturned:
            # If multiple users found (shouldn't happen with proper constraints),
            # get the first one
            user = User.objects.filter(
                Q(username__iexact=username) | Q(email__iexact=username)
            ).first()
        
        # Check password using Django's default password checker
        if user and user.check_password(password) and self.user_can_authenticate(user):
            return user
        
        return None
    
    def get_user(self, user_id):
        """
        Retrieve a user by their ID.
        
        Args:
            user_id: The user's ID
            
        Returns:
            User object if found and active, None otherwise
        """
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        
        return user if self.user_can_authenticate(user) else None

