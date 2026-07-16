"""
Device Detection and Tracking Utilities
"""
import re
import requests
import logging
from user_agents import parse
from django.core.cache import cache
import hashlib

logger = logging.getLogger('accounts')


def get_client_ip(request):
    """
    Extract client IP address from request, handling proxies and local development
    """
    # Try various headers that might contain the real client IP
    headers_to_check = [
        'HTTP_X_FORWARDED_FOR',
        'HTTP_X_REAL_IP',
        'HTTP_CF_CONNECTING_IP',  # Cloudflare
        'HTTP_X_FORWARDED',
        'HTTP_FORWARDED_FOR',
        'HTTP_FORWARDED',
    ]
    
    for header in headers_to_check:
        ip = request.META.get(header)
        if ip:
            # X-Forwarded-For can contain multiple IPs, get the first one
            if ',' in ip:
                ip = ip.split(',')[0].strip()
            # Validate it's not a local IP
            if ip and ip not in ['127.0.0.1', 'localhost', '::1']:
                return ip
    
    # Fallback to REMOTE_ADDR
    ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


def get_location_from_ip(ip_address):
    """
    Get location information from IP address using ip-api.com
    Free tier: 45 requests per minute
    """
    # Handle local/private IPs
    if not ip_address or ip_address in ['127.0.0.1', 'localhost', '::1']:
        # For development, try to get server's public IP and use that
        try:
            pub_ip_response = requests.get('https://api.ipify.org?format=json', timeout=2)
            if pub_ip_response.status_code == 200:
                public_ip = pub_ip_response.json().get('ip')
                if public_ip:
                    # Try to get location for server's public IP
                    location = get_location_from_ip(public_ip)
                    if location and location.get('country') != 'Unknown':
                        # Add note that this is dev mode
                        location['country'] = f"{location['country']} (Dev Mode)"
                        location['full_location'] = f"{location['city']}, {location['country']}"
                        return location
        except:
            pass
        
        return {
            'country': 'Development',
            'city': 'Local',
            'full_location': 'Local Development (Testing Mode)'
        }
    
    # Check if it's a private IP range
    private_ranges = [
        '10.', '172.16.', '172.17.', '172.18.', '172.19.', '172.20.',
        '172.21.', '172.22.', '172.23.', '172.24.', '172.25.', '172.26.',
        '172.27.', '172.28.', '172.29.', '172.30.', '172.31.', '192.168.'
    ]
    if any(ip_address.startswith(prefix) for prefix in private_ranges):
        return {
            'country': 'Private Network',
            'city': 'Local',
            'full_location': 'Private Network (Local Testing)'
        }
    
    # Check cache first
    cache_key = f'ip_location_{ip_address}'
    cached_location = cache.get(cache_key)
    if cached_location:
        return cached_location
    
    try:
        response = requests.get(
            f'http://ip-api.com/json/{ip_address}',
            timeout=3
        )
        if response.status_code == 200:
            data = response.json()
            if data.get('status') == 'success':
                location = {
                    'country': data.get('country', 'Unknown'),
                    'city': data.get('city', 'Unknown'),
                    'full_location': f"{data.get('city', 'Unknown')}, {data.get('country', 'Unknown')}"
                }
                # Cache for 24 hours
                cache.set(cache_key, location, 86400)
                return location
    except Exception as e:
        logger.warning(f"Error fetching location for IP {ip_address}: {e}")
    
    return {
        'country': 'Unknown',
        'city': 'Unknown',
        'full_location': 'Unknown Location'
    }


def parse_user_agent(user_agent_string):
    """
    Parse user agent string to extract device information
    """
    if not user_agent_string:
        return {
            'device_type': 'unknown',
            'platform': 'unknown',
            'browser': 'Unknown',
            'device_name': None,
        }
    
    user_agent = parse(user_agent_string)
    
    # Determine device type
    if user_agent.is_mobile:
        device_type = 'mobile'
    elif user_agent.is_tablet:
        device_type = 'tablet'
    elif user_agent.is_pc:
        device_type = 'desktop'
    else:
        device_type = 'web'
    
    # Determine platform
    if user_agent.os.family:
        os_family = user_agent.os.family.lower()
        if 'ios' in os_family or 'iphone' in os_family:
            platform = 'ios'
        elif 'android' in os_family:
            platform = 'android'
        elif 'windows' in os_family:
            platform = 'windows'
        elif 'mac' in os_family or 'os x' in os_family:
            platform = 'macos'
        elif 'linux' in os_family:
            platform = 'linux'
        else:
            platform = 'web'
    else:
        platform = 'unknown'
    
    # Get browser info
    browser = f"{user_agent.browser.family} {user_agent.browser.version_string}" if user_agent.browser.family else "Unknown"
    
    # Get device name
    device_name = None
    if user_agent.device.family and user_agent.device.family != 'Other':
        device_name = user_agent.device.family
        if user_agent.device.brand:
            device_name = f"{user_agent.device.brand} {device_name}"
    
    return {
        'device_type': device_type,
        'platform': platform,
        'browser': browser,
        'device_name': device_name,
    }


def generate_device_fingerprint(request):
    """
    Generate a unique fingerprint for the device
    Based on user agent and stable headers only - NOT IP address
    
    IMPORTANT: We intentionally exclude IP address because:
    - Mobile users frequently change IPs (WiFi to cellular, different locations)
    - The same physical device should maintain the same fingerprint
    - IP changes would create duplicate device records
    
    For better device identification on mobile apps, the app should send
    a device-specific identifier in the X-Device-ID header.
    """
    user_agent = request.META.get('HTTP_USER_AGENT', '')
    accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    
    # Check for client-provided device ID (from mobile apps)
    # This is the most reliable way to identify a device
    device_id = request.META.get('HTTP_X_DEVICE_ID', '')
    
    # Parse user agent to extract stable device information
    ua_info = parse_user_agent(user_agent)
    
    # Create stable fingerprint components
    # Use parsed UA info instead of raw UA to be more resilient to browser version updates
    stable_components = [
        ua_info.get('platform', ''),
        ua_info.get('device_type', ''),
        ua_info.get('device_name', '') or '',
        accept_language,
    ]
    
    # If device ID is provided by the app, use it as primary identifier
    if device_id:
        stable_components.insert(0, device_id)
    else:
        # Fallback: use user agent string but try to make it more stable
        # by removing version numbers that change frequently
        stable_ua = normalize_user_agent(user_agent)
        stable_components.append(stable_ua)
    
    fingerprint_string = '|'.join(stable_components)
    fingerprint = hashlib.sha256(fingerprint_string.encode()).hexdigest()[:32]
    
    return fingerprint


def normalize_user_agent(user_agent):
    """
    Normalize user agent by removing version numbers that change frequently
    This makes the fingerprint more stable across app updates
    """
    import re
    
    if not user_agent:
        return ''
    
    # Remove common version patterns like /1.2.3, v1.2.3, (1.2.3), etc.
    # Keep the main identifying parts
    normalized = re.sub(r'/[\d.]+', '', user_agent)
    normalized = re.sub(r'\s[\d.]+\s', ' ', normalized)
    normalized = re.sub(r'\([\d.]+\)', '', normalized)
    
    # Remove build numbers and hashes
    normalized = re.sub(r'Build/[A-Za-z0-9.]+', '', normalized)
    normalized = re.sub(r'[A-F0-9]{8,}', '', normalized)
    
    # Clean up extra spaces
    normalized = ' '.join(normalized.split())
    
    return normalized.strip()


def get_device_info_from_request(request):
    """
    Extract comprehensive device information from Django request
    """
    user_agent_string = request.META.get('HTTP_USER_AGENT', '')
    ip_address = get_client_ip(request)
    
    # Parse user agent
    ua_info = parse_user_agent(user_agent_string)
    
    # Get location
    location_info = get_location_from_ip(ip_address)
    
    # Generate fingerprint
    fingerprint = generate_device_fingerprint(request)
    
    # Check for device info sent by mobile app
    # These headers provide more accurate info than user agent parsing
    app_device_name = request.META.get('HTTP_X_DEVICE_NAME', '')
    app_platform = request.META.get('HTTP_X_DEVICE_PLATFORM', '')
    
    # Use app-provided info if available (more accurate for mobile apps)
    device_name = app_device_name or ua_info['device_name']
    platform = app_platform or ua_info['platform']
    
    # If platform is provided by app, normalize it
    if app_platform:
        platform = app_platform.lower()
        if platform not in ('ios', 'android', 'windows', 'macos', 'linux', 'web'):
            platform = ua_info['platform']  # fallback to parsed UA
    
    return {
        'device_type': ua_info['device_type'],
        'platform': platform,
        'device_name': device_name,
        'browser': ua_info['browser'],
        'ip_address': ip_address,
        'country': location_info['country'],
        'city': location_info['city'],
        'user_agent': user_agent_string,
        'device_fingerprint': fingerprint,
    }


def should_create_new_device_record(user, fingerprint):
    """
    Determine if we should create a new device record or update existing
    """
    from accounts.device_models import UserDevice
    
    # Check if device with this fingerprint exists for this user
    existing_device = UserDevice.objects.filter(
        user=user,
        device_fingerprint=fingerprint
    ).first()
    
    return existing_device is None, existing_device