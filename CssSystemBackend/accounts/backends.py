"""
Custom authentication backend for phone number normalization.
This backend allows users to login with various phone number formats:
- 0597959032
- 597959032
- +233597959032
- 233597959032
All will be normalized to +233597959032 before authentication.
"""
from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from accounts.repository import UserRepository


class PhoneNumberAuthBackend(ModelBackend):
    """
    Custom authentication backend that normalizes phone numbers before authentication.
    This works with Django admin login.
    """
    
    def authenticate(self, request, username=None, password=None, **kwargs):
        """
        Authenticate user by normalizing the phone number (username field).
        """
        UserModel = get_user_model()
        
        if username is None:
            username = kwargs.get(UserModel.USERNAME_FIELD)
        
        if username is None or password is None:
            return None
        
        # Normalize the phone number
        normalized_phone = UserRepository.normalize_phone(username)
        
        try:
            # Try to fetch the user with normalized phone
            user = UserModel.objects.get(phone=normalized_phone)
        except UserModel.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user (#20760).
            UserModel().set_password(password)
            return None
        else:
            # Check password and return user if valid
            if user.check_password(password) and self.user_can_authenticate(user):
                return user
        
        return None
    
    def get_user(self, user_id):
        """
        Get user by ID. This is required by Django's authentication framework.
        """
        UserModel = get_user_model()
        try:
            return UserModel.objects.get(pk=user_id)
        except UserModel.DoesNotExist:
            return None
