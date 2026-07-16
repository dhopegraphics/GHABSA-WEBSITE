"""
Device Access Middleware
Checks if a device is blocked before allowing access
"""
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin
from accounts.device_models import UserDevice
from accounts.device_utils import generate_device_fingerprint
import logging

logger = logging.getLogger(__name__)


class BlockedDeviceMiddleware(MiddlewareMixin):
    """
    Middleware to check if the requesting device is blocked
    """
    
    # Exempt paths that should always be accessible
    EXEMPT_PATHS = [
        '/accounts/obtain-token/',  # Login endpoint
        '/accounts/register/',
        '/accounts/request-forgot-password/',
        '/accounts/reset-password/',
        '/accounts/refresh-token/',
        '/accounts/verify-token/',
        '/admin/',
        '/static/',
        '/media/',
    ]
    
    def process_request(self, request):
        """Check if device is blocked before processing request"""
        
        # Skip unauthenticated requests
        if not hasattr(request, 'user') or not request.user.is_authenticated:
            return None
        
        # Skip exempt paths
        path = request.path
        if any(path.startswith(exempt) for exempt in self.EXEMPT_PATHS):
            return None
        
        try:
            # Generate device fingerprint using request object
            device_fingerprint = generate_device_fingerprint(request)
            
            # Check if this device is blocked
            blocked_device = UserDevice.objects.filter(
                user=request.user,
                device_fingerprint=device_fingerprint,
                is_blocked=True
            ).first()
            
            if blocked_device:
                logger.warning(
                    f"Blocked device attempt: User {request.user.phone}, "
                    f"Device: {blocked_device.get_device_display()}, "
                    f"Reason: {blocked_device.block_reason or 'No reason provided'}"
                )
                
                return JsonResponse({
                    'status': 'error',
                    'code': 'DEVICE_BLOCKED',
                    'message': 'This device has been blocked from accessing your account.',
                    'details': {
                        'device': blocked_device.get_device_display(),
                        'blocked_at': blocked_device.blocked_at.isoformat() if blocked_device.blocked_at else None,
                        'reason': blocked_device.block_reason or 'No reason provided'
                    }
                }, status=403)
        
        except Exception as e:
            logger.error(f"Error in BlockedDeviceMiddleware: {str(e)}")
            # Don't block request if there's an error in middleware
            pass
        
        return None
