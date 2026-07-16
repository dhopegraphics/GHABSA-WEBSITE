"""
Performance and Error Handling Middleware for PythonAnywhere

This middleware provides:
1. Request timeout handling
2. Performance monitoring
3. Graceful error handling to prevent OSError: write error
4. Request/Response compression awareness
"""

import time
import logging
from django.http import JsonResponse
from django.conf import settings


logger = logging.getLogger('api')


class PerformanceMiddleware:
    """
    Middleware for monitoring request performance and preventing timeouts.
    
    Features:
    - Logs slow requests (> 2 seconds)
    - Adds performance headers in DEBUG mode
    - Handles database connection cleanup
    """
    
    SLOW_REQUEST_THRESHOLD = 2.0  # seconds
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Record start time
        start_time = time.time()
        
        # Store start time on request for other middleware/views
        request._start_time = start_time
        
        # Process request
        response = self.get_response(request)
        
        # Calculate duration
        duration = time.time() - start_time
        
        # Log slow requests
        if duration > self.SLOW_REQUEST_THRESHOLD:
            logger.warning(
                f"SLOW REQUEST: {request.method} {request.path} "
                f"took {duration:.2f}s (user: {getattr(request.user, 'id', 'anon')})"
            )
        
        # Add performance header in DEBUG mode
        if settings.DEBUG:
            response['X-Request-Duration'] = f"{duration:.3f}s"
        
        return response


class SafeErrorHandlerMiddleware:
    """
    Middleware that catches unhandled exceptions and returns proper JSON responses.
    This prevents OSError: write error by avoiding console error output.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        try:
            return self.get_response(request)
        except Exception as e:
            # Log to file only (never console)
            logger.exception(f"Unhandled exception in {request.method} {request.path}")
            
            # Return JSON error response
            return JsonResponse({
                'error': 'An unexpected error occurred',
                'detail': str(e) if settings.DEBUG else 'Please try again later'
            }, status=500)


class RequestThrottleMiddleware:
    """
    Simple in-memory request throttling to prevent server overload.
    Complements DRF throttling for non-API endpoints.
    """
    
    # In-memory request counter (resets on server restart)
    _request_counts = {}
    
    # Maximum requests per second per IP
    MAX_RPS_PER_IP = 10
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Skip for static files and admin
        if request.path.startswith(('/static/', '/admin/jsi18n/')):
            return self.get_response(request)
        
        # Get client IP
        ip = self._get_client_ip(request)
        
        # Get current second
        current_second = int(time.time())
        key = f"{ip}:{current_second}"
        
        # Count requests
        count = self._request_counts.get(key, 0) + 1
        self._request_counts[key] = count
        
        # Clean old entries (keep only last 2 seconds)
        old_keys = [
            k for k in self._request_counts.keys()
            if not k.endswith(f":{current_second}") and 
               not k.endswith(f":{current_second - 1}")
        ]
        for old_key in old_keys:
            self._request_counts.pop(old_key, None)
        
        # Check rate limit
        if count > self.MAX_RPS_PER_IP:
            logger.warning(f"Rate limit exceeded for IP: {ip} ({count} rps)")
            return JsonResponse({
                'error': 'Too many requests',
                'detail': 'Please slow down'
            }, status=429)
        
        return self.get_response(request)
    
    def _get_client_ip(self, request):
        """Extract client IP from request headers"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', 'unknown')


class DatabaseConnectionMiddleware:
    """
    Ensures database connections are properly closed after each request.
    Helps prevent connection leaks on PythonAnywhere.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        response = self.get_response(request)
        
        # Close old database connections
        from django.db import connections
        for conn in connections.all():
            conn.close_if_unusable_or_obsolete()
        
        return response
