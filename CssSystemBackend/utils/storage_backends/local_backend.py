"""
Local File Storage Backend

Stores files on the local file system using Django's MEDIA_ROOT.
Good for development, self-hosted servers (PythonAnywhere, VPS, etc.),
and as a fallback when cloud storage is unavailable.

This backend is always available as a fallback option.
"""

import os
import re
import hashlib
import logging
from typing import Optional, Union, Dict, Any, BinaryIO, Tuple
from datetime import datetime
from urllib.parse import urljoin

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from .base import StorageBackend

logger = logging.getLogger(__name__)


def sanitize_filename(filename: str) -> str:
    """
    Sanitize filename to be URL-safe and filesystem-safe.
    
    - Replaces spaces with underscores
    - Removes special characters except underscores, hyphens, and periods
    - Ensures filename is not too long
    """
    if not filename:
        return filename
    
    # Get the base name and extension
    base, ext = os.path.splitext(filename)
    
    # Replace spaces with underscores
    base = base.replace(' ', '_')
    
    # Remove any characters that aren't alphanumeric, underscore, or hyphen
    base = re.sub(r'[^\w\-]', '', base)
    
    # Ensure base is not empty
    if not base:
        base = hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]
    
    # Limit length (keep last 50 chars of base to preserve uniqueness)
    if len(base) > 50:
        base = base[-50:]
    
    return f"{base}{ext.lower()}"


class LocalStorageBackend(StorageBackend):
    """
    Local file system storage backend.
    Stores files in Django's MEDIA_ROOT and serves via MEDIA_URL.
    
    Setup:
    Configure in settings.py:
    
        MEDIA_ROOT = BASE_DIR / 'media'
        MEDIA_URL = '/media/'
        
        # REQUIRED: Full URL for the site (used to generate absolute URLs)
        # Local: SITE_URL = 'http://127.0.0.1:8000'
        # Production: SITE_URL = 'https://api.biochemknust.com'
        SITE_URL = 'https://your-domain.com'
    
    Features:
    - No external dependencies
    - Works offline
    - Automatic directory creation
    - Date-based file organization
    - Always generates full absolute URLs (SITE_URL + MEDIA_URL + path)
    """
    
    name = "local"
    
    def __init__(self):
        self.media_root = getattr(settings, 'MEDIA_ROOT', '')
        self.media_url = getattr(settings, 'MEDIA_URL', '/media/')
        self.base_url = getattr(settings, 'SITE_URL', '') or getattr(settings, 'BASE_URL', '')
        
        # Log warning if SITE_URL is not set
        if not self.base_url:
            logger.warning(
                "SITE_URL is not set in settings. Local storage will generate relative URLs. "
                "Set SITE_URL to generate full absolute URLs (e.g., SITE_URL='http://127.0.0.1:8000' for local dev, "
                "SITE_URL='https://api.biochemknust.com' for production)."
            )
    
    def is_available(self) -> bool:
        """Check if local storage is configured."""
        return bool(self.media_root)
    
    def _get_upload_path(self, folder: str, filename: str) -> Tuple[str, str]:
        """
        Generate upload path and ensure directory exists.
        Returns (full_path, relative_path)
        """
        date_path = datetime.now().strftime('%Y/%m')
        
        if folder:
            relative_dir = os.path.join(folder, date_path)
        else:
            relative_dir = date_path
        
        full_dir = os.path.join(self.media_root, relative_dir)
        os.makedirs(full_dir, exist_ok=True)
        
        base, ext = os.path.splitext(filename)
        counter = 0
        final_filename = filename
        
        while os.path.exists(os.path.join(full_dir, final_filename)):
            counter += 1
            final_filename = f"{base}_{counter}{ext}"
        
        full_path = os.path.join(full_dir, final_filename)
        relative_path = os.path.join(relative_dir, final_filename)
        
        return full_path, relative_path
    
    def upload(
        self,
        file: Union[BinaryIO, UploadedFile, bytes],
        folder: str = "",
        filename: Optional[str] = None,
        resource_type: str = "image",
        **options
    ) -> Dict[str, Any]:
        """Upload file to local storage."""
        if not self.is_available():
            return {
                'success': False,
                'error': 'Local storage is not configured (MEDIA_ROOT not set)',
                'url': None,
                'provider': self.name,
            }
        
        try:
            if filename is None:
                if hasattr(file, 'name'):
                    filename = os.path.basename(file.name)
                else:
                    ext = '.bin'
                    if resource_type == 'image':
                        ext = '.jpg'
                    elif resource_type == 'video':
                        ext = '.mp4'
                    filename = f"{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]}{ext}"
            
            # Log the incoming folder and filename
            logger.info(f"LocalStorage.upload - folder: '{folder}', filename: '{filename}'")
            
            # Sanitize filename to be URL-safe
            filename = sanitize_filename(filename)
            
            logger.info(f"LocalStorage.upload - sanitized filename: '{filename}'")
            
            full_path, relative_path = self._get_upload_path(folder, filename)
            
            logger.info(f"LocalStorage.upload - full_path: '{full_path}', relative_path: '{relative_path}'")
            
            with open(full_path, 'wb') as dest:
                if isinstance(file, bytes):
                    dest.write(file)
                    file_size = len(file)
                elif hasattr(file, 'chunks'):
                    file_size = 0
                    for chunk in file.chunks():
                        dest.write(chunk)
                        file_size += len(chunk)
                elif hasattr(file, 'read'):
                    content = file.read()
                    dest.write(content)
                    file_size = len(content)
                else:
                    return {
                        'success': False,
                        'error': 'Invalid file type',
                        'url': None,
                        'provider': self.name,
                    }
            
            url_path = relative_path.replace('\\', '/')
            relative_url = urljoin(self.media_url, url_path)
            
            # Always generate full absolute URL if SITE_URL is set
            if self.base_url:
                full_url = urljoin(self.base_url, relative_url)
            else:
                # Return relative URL but log warning
                full_url = relative_url
                logger.warning(
                    f"Generated relative URL '{relative_url}' because SITE_URL is not set. "
                    f"Set SITE_URL in settings or .env to generate absolute URLs."
                )
            
            logger.info(f"Local storage: Uploaded file to {full_url}")
            
            return {
                'success': True,
                'url': full_url,
                'public_id': relative_path,
                'resource_type': resource_type,
                'format': os.path.splitext(filename)[1].lstrip('.'),
                'size': file_size,
                'local_path': full_path,
                'provider': self.name,
            }
            
        except Exception as e:
            logger.error(f"Local storage upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': None,
                'provider': self.name,
            }
    
    def delete(self, public_id: str, resource_type: str = "image") -> bool:
        """Delete file from local storage."""
        try:
            full_path = os.path.join(self.media_root, public_id)
            if os.path.exists(full_path):
                os.remove(full_path)
                return True
            return False
        except Exception as e:
            logger.error(f"Local storage delete failed: {e}")
            return False
    
    def get_url(
        self,
        identifier: str,
        resource_type: str = "image",
        **transformations
    ) -> Optional[str]:
        """Get URL for local file."""
        url_path = identifier.replace('\\', '/')
        relative_url = urljoin(self.media_url, url_path)
        
        if self.base_url:
            return urljoin(self.base_url, relative_url)
        return relative_url
