"""
Repository for Device Management
"""
from accounts.device_models import UserDevice, DeviceLoginHistory
from django.utils import timezone
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)


class UserDeviceRepository:
    """Repository for managing user devices"""
    
    @staticmethod
    def create_or_update_device(user, device_info, refresh_token_jti=None):
        """
        Create new device record or update existing one.
        
        Uses a multi-tier matching strategy:
        1. First, try to match by fingerprint (most precise)
        2. If no match, try to match by similar device characteristics
           (same platform, device_type, and similar user_agent pattern)
        3. Only create a new device if no good match is found
        """
        fingerprint = device_info.get('device_fingerprint')
        device_type = device_info.get('device_type', 'unknown')
        platform = device_info.get('platform', 'unknown')
        device_name = device_info.get('device_name')
        user_agent = device_info.get('user_agent', '')
        
        # Tier 1: Try to find existing device by fingerprint
        device = UserDevice.objects.filter(
            user=user,
            device_fingerprint=fingerprint
        ).first()
        
        if device:
            logger.debug(f"Device matched by fingerprint for user {user.id}")
            return UserDeviceRepository._update_existing_device(
                device, device_info, refresh_token_jti
            )
        
        # Tier 2: Try to find similar device that might be the same physical device
        # This helps when fingerprint changes due to app updates or browser changes
        similar_device = UserDeviceRepository._find_similar_device(
            user, device_type, platform, device_name, user_agent
        )
        
        if similar_device:
            logger.info(
                f"Device matched by similarity for user {user.id}: "
                f"{similar_device.get_device_display()}"
            )
            # Update the fingerprint to the new one
            similar_device.device_fingerprint = fingerprint
            return UserDeviceRepository._update_existing_device(
                similar_device, device_info, refresh_token_jti
            )
        
        # Tier 3: No match found, create new device
        logger.info(f"Creating new device for user {user.id}: {platform} {device_type}")
        device = UserDevice.objects.create(
            user=user,
            device_type=device_type,
            platform=platform,
            device_name=device_name,
            browser=device_info.get('browser'),
            ip_address=device_info.get('ip_address'),
            country=device_info.get('country'),
            city=device_info.get('city'),
            user_agent=user_agent,
            device_fingerprint=fingerprint,
            refresh_token_jti=refresh_token_jti,
            is_active=True,
        )
        
        # Mark as current device
        device.mark_as_current()
        
        return device
    
    @staticmethod
    def _update_existing_device(device, device_info, refresh_token_jti=None):
        """Update an existing device with new info"""
        device.last_active = timezone.now()
        device.ip_address = device_info.get('ip_address')
        device.country = device_info.get('country')
        device.city = device_info.get('city')
        device.is_active = True
        
        # Update user agent if changed (app updates, etc.)
        if device_info.get('user_agent'):
            device.user_agent = device_info.get('user_agent')
        
        # Update browser info if available
        if device_info.get('browser'):
            device.browser = device_info.get('browser')
        
        if refresh_token_jti:
            device.refresh_token_jti = refresh_token_jti
        
        device.save()
        device.mark_as_current()
        
        return device
    
    @staticmethod
    def _find_similar_device(user, device_type, platform, device_name, user_agent):
        """
        Find a device that is likely the same physical device based on characteristics.
        
        Matching criteria:
        - Same platform (ios, android, etc.)
        - Same device type (mobile, tablet, desktop)
        - Either same device name OR similar user agent pattern
        """
        # Build the base query
        base_query = Q(user=user, platform=platform, device_type=device_type)
        
        # Try to match by device name first (most reliable for named devices)
        if device_name:
            device_by_name = UserDevice.objects.filter(
                base_query,
                device_name=device_name
            ).order_by('-last_active').first()
            
            if device_by_name:
                return device_by_name
        
        # For mobile apps, try matching by user agent pattern
        # Mobile apps typically have consistent UA patterns even across versions
        if user_agent and platform in ('ios', 'android'):
            # Extract app identifier from user agent if present
            app_identifier = UserDeviceRepository._extract_app_identifier(user_agent)
            
            if app_identifier:
                # Find devices with similar user agent pattern
                similar_devices = UserDevice.objects.filter(
                    base_query,
                    user_agent__icontains=app_identifier
                ).order_by('-last_active')
                
                if similar_devices.exists():
                    return similar_devices.first()
        
        return None
    
    @staticmethod
    def _extract_app_identifier(user_agent):
        """
        Extract a stable app identifier from the user agent string.
        
        For mobile apps, this might be the app name or bundle identifier.
        """
        if not user_agent:
            return None
        
        # Common patterns for mobile apps
        # Look for app-specific identifiers that remain stable across versions
        import re
        
        # Match patterns like "AppName/", "com.company.app", etc.
        patterns = [
            r'([\w.-]+/[\d.]+)\s',  # AppName/1.0.0
            r'(com\.[\w.]+)',        # com.company.app
            r'(Expo(?:Go)?)',        # Expo or ExpoGo
            r'(okhttp|Axios)',       # HTTP clients used by React Native
        ]
        
        for pattern in patterns:
            match = re.search(pattern, user_agent, re.IGNORECASE)
            if match:
                # Return just the identifier part, not version
                identifier = match.group(1).split('/')[0]
                if len(identifier) > 3:  # Avoid matching very short strings
                    return identifier
        
        return None
    
    @staticmethod
    def get_user_devices(user, active_only=True):
        """
        Get all devices for a user
        """
        queryset = UserDevice.objects.filter(user=user)
        if active_only:
            queryset = queryset.filter(is_active=True)
        return queryset.order_by('-last_active')
    
    @staticmethod
    def get_device_by_id(device_id, user):
        """
        Get specific device by ID for a user
        """
        return UserDevice.objects.filter(id=device_id, user=user).first()
    
    @staticmethod
    def deactivate_device(device_id, user):
        """
        Deactivate a specific device
        """
        device = UserDevice.objects.filter(id=device_id, user=user).first()
        if device:
            device.deactivate()
            return True
        return False
    
    @staticmethod
    def deactivate_all_except_current(user, current_device_id):
        """
        Deactivate all devices except the current one
        """
        UserDevice.objects.filter(user=user).exclude(id=current_device_id).update(
            is_active=False,
            is_current=False
        )
    
    @staticmethod
    def mark_device_as_trusted(device_id, user):
        """
        Mark device as trusted
        """
        device = UserDevice.objects.filter(id=device_id, user=user).first()
        if device:
            device.is_trusted = True
            device.save()
            return True
        return False
    
    @staticmethod
    def get_current_device(user):
        """
        Get the current active device for user
        """
        return UserDevice.objects.filter(user=user, is_current=True).first()


class DeviceLoginHistoryRepository:
    """Repository for managing login history"""
    
    @staticmethod
    def record_login(device, user, ip_address, location, success=True, reason=None):
        """
        Record a login attempt
        """
        return DeviceLoginHistory.objects.create(
            device=device,
            user=user,
            ip_address=ip_address,
            location=location,
            success=success,
            reason=reason
        )
    
    @staticmethod
    def get_user_login_history(user, limit=50):
        """
        Get login history for a user
        """
        return DeviceLoginHistory.objects.filter(user=user).order_by('-login_time')[:limit]
    
    @staticmethod
    def get_device_login_history(device, limit=20):
        """
        Get login history for a specific device
        """
        return DeviceLoginHistory.objects.filter(device=device).order_by('-login_time')[:limit]
