"""
Utility functions for projects app
"""
import re


def convert_to_direct_image_url(url):
    """
    Convert Google Drive and Dropbox share links to direct image URLs
    
    Args:
        url: The share URL from Google Drive or Dropbox
        
    Returns:
        Direct image URL that can be accessed without authentication
    """
    if not url:
        return url
    
    # Handle Google Drive links
    # Format: https://drive.google.com/file/d/FILE_ID/view
    # Convert to: https://drive.google.com/uc?export=view&id=FILE_ID
    google_drive_patterns = [
        r'https://drive\.google\.com/file/d/([a-zA-Z0-9_-]+)',
        r'https://drive\.google\.com/open\?id=([a-zA-Z0-9_-]+)',
    ]
    
    for pattern in google_drive_patterns:
        match = re.search(pattern, url)
        if match:
            file_id = match.group(1)
            return f'https://drive.google.com/uc?export=view&id={file_id}'
    
    # Handle Dropbox links
    # Format: https://www.dropbox.com/s/FILE_ID/filename?dl=0
    # Convert to: https://www.dropbox.com/s/FILE_ID/filename?raw=1
    if 'dropbox.com' in url:
        # Replace dl=0 with raw=1 or dl=1 with raw=1
        url = re.sub(r'[?&]dl=[01]', '', url)
        if '?' in url:
            url = url + '&raw=1'
        else:
            url = url + '?raw=1'
        return url
    
    # If it's already a direct link or from another service, return as is
    return url


def extract_file_id_from_url(url):
    """
    Extract file ID from Google Drive or Dropbox URLs
    Useful for validation and tracking
    """
    if not url:
        return None
    
    # Google Drive
    google_match = re.search(r'drive\.google\.com.*[/=]([a-zA-Z0-9_-]+)', url)
    if google_match:
        return google_match.group(1)
    
    # Dropbox
    dropbox_match = re.search(r'dropbox\.com/s/([a-zA-Z0-9_-]+)', url)
    if dropbox_match:
        return dropbox_match.group(1)
    
    return None


def is_cloud_storage_url(url):
    """
    Check if URL is from a cloud storage service
    """
    if not url:
        return False
    
    cloud_services = [
        'drive.google.com',
        'dropbox.com',
        'onedrive.live.com',
        'box.com',
    ]
    
    return any(service in url.lower() for service in cloud_services)
