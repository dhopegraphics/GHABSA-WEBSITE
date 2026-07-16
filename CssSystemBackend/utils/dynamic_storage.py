"""
Dynamic Storage Backend for Django Models

This module provides a custom Django storage class that integrates with our
MediaStorage system, allowing ImageField and FileField to automatically use
the configured storage backend (local, Google Drive, S3, Cloudinary, etc.)

Usage:
    # In your model:
    from utils.dynamic_storage import DynamicStorage
    
    class Product(models.Model):
        # Basic usage - uses default backend from settings
        image = models.ImageField(storage=DynamicStorage(), upload_to='products/')
        
        # Or use model-specific backend
        image = models.ImageField(storage=DynamicStorage(backend='google_drive'), upload_to='products/')

    # Or set globally in settings.py:
    DEFAULT_FILE_STORAGE = 'utils.dynamic_storage.DynamicStorage'
"""

import os
import re
import hashlib
import logging
from datetime import datetime
from io import BytesIO
from typing import Optional, Any

from django.conf import settings
from django.core.files.base import ContentFile, File
from django.core.files.storage import Storage
from django.utils.deconstruct import deconstructible

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


@deconstructible
class DynamicStorage(Storage):
    """
    Custom Django storage backend that routes uploads to the configured
    storage provider (local, Google Drive, S3, Cloudinary, etc.)
    
    This storage class integrates with the MediaStorage system to provide:
    - Automatic backend selection based on settings
    - Model-specific backend override
    - Full URL generation for API responses
    - Seamless fallback between backends
    """
    
    def __init__(self, backend: Optional[str] = None, **kwargs):
        """
        Initialize DynamicStorage.
        
        Args:
            backend: Specific backend to use. If None, uses MEDIA_STORAGE_BACKEND setting.
                    Options: 'local', 'cloudinary', 'google_drive', 's3', 'dropbox', 
                            'azure_blob', 'backblaze_b2'
        """
        super().__init__()
        self._backend_name = backend
        self._storage = None
    
    def __eq__(self, other):
        return isinstance(other, DynamicStorage) and self._backend_name == other._backend_name
    
    def __hash__(self):
        return hash(self._backend_name)
    
    @property
    def storage(self):
        """Lazy-load the storage backend."""
        if self._storage is None:
            from utils.media_storage import AVAILABLE_BACKENDS
            from django.conf import settings as django_settings
            
            # Determine which backend to use
            backend_name = self._backend_name or getattr(django_settings, 'MEDIA_STORAGE_BACKEND', 'local')
            
            if backend_name in AVAILABLE_BACKENDS:
                backend_class = AVAILABLE_BACKENDS[backend_name]
                self._storage = backend_class()
                if not self._storage.is_available():
                    logger.warning(f"Backend '{backend_name}' not available, falling back to local")
                    self._storage = AVAILABLE_BACKENDS['local']()
            else:
                logger.warning(f"Unknown backend '{backend_name}', using local")
                self._storage = AVAILABLE_BACKENDS['local']()
        
        return self._storage
    
    def _save(self, name: str, content: File) -> str:
        """
        Save the file to storage.
        
        Args:
            name: The file name/path
            content: The file content
        
        Returns:
            The name of the saved file
        """
        try:
            # Log the incoming name
            logger.info(f"DynamicStorage._save called with name: {name}")
            
            # Extract folder and filename from name
            folder = os.path.dirname(name).replace('\\', '/')
            filename = os.path.basename(name)
            
            logger.info(f"Extracted folder: '{folder}', filename: '{filename}'")
            
            # Sanitize filename to be URL-safe
            filename = sanitize_filename(filename)
            
            logger.info(f"Sanitized filename: '{filename}'")
            
            # Determine resource type
            resource_type = 'image'
            ext = os.path.splitext(filename)[1].lower()
            if ext in ['.mp4', '.avi', '.mov', '.webm', '.mkv']:
                resource_type = 'video'
            elif ext in ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx', '.txt', '.zip']:
                resource_type = 'raw'
            
            # Read file content
            if hasattr(content, 'read'):
                content.seek(0)
                file_data = content.read()
                content.seek(0)  # Reset for potential re-read
            else:
                file_data = content
            
            # Create a BytesIO object for upload
            file_obj = BytesIO(file_data)
            file_obj.name = filename
            
            # Upload to storage backend
            result = self.storage.upload(
                file=file_obj,
                folder=folder,
                filename=filename,
                resource_type=resource_type,
            )
            
            if result.get('success'):
                url = result.get('url', '')
                public_id = result.get('public_id', '')
                local_path = result.get('local_path', '')
                
                logger.info(f"Uploaded {filename} to {self.storage.name}: {url}")
                
                # For local storage, return the relative path (public_id) so that
                # Django can properly resolve file paths for deletion, etc.
                # For cloud storage, return the URL since there's no local path.
                if local_path or (self.storage.name == 'local'):
                    # Local storage - return relative path
                    stored_name = public_id if public_id else name
                    logger.info(f"Local storage - returning relative path: {stored_name}")
                    return stored_name
                else:
                    # Cloud storage - return URL
                    logger.info(f"Cloud storage - returning URL: {url}")
                    return url
            else:
                error = result.get('error', 'Unknown error')
                logger.error(f"Upload failed: {error}")
                raise IOError(f"Failed to upload file: {error}")
                
        except Exception as e:
            logger.error(f"Error saving file {name}: {e}")
            raise
    
    def _open(self, name: str, mode: str = 'rb') -> File:
        """
        Open a file from storage.
        
        For cloud storage backends, this downloads the file content.
        """
        try:
            # If name is a URL, try to download it
            if name.startswith(('http://', 'https://')):
                import requests
                response = requests.get(name, timeout=30)
                response.raise_for_status()
                return ContentFile(response.content, name=os.path.basename(name))
            
            # For local storage, use the local backend
            if hasattr(self.storage, 'open'):
                return self.storage.open(name, mode)
            
            # Fallback: try to read from MEDIA_ROOT
            path = os.path.join(settings.MEDIA_ROOT, name)
            return File(open(path, mode))
            
        except Exception as e:
            logger.error(f"Error opening file {name}: {e}")
            raise
    
    def delete(self, name: str) -> None:
        """Delete a file from storage."""
        try:
            if name:
                # Extract public_id from URL if needed
                self.storage.delete(name)
                logger.info(f"Deleted file: {name}")
        except Exception as e:
            logger.error(f"Error deleting file {name}: {e}")
    
    def exists(self, name: str) -> bool:
        """
        Check if a file exists.
        For URLs, we assume they exist (or we'd need to make HTTP requests).
        """
        if not name:
            return False
        
        # For URLs, assume they exist
        if name.startswith(('http://', 'https://')):
            return True
        
        # For local files, check the filesystem
        if hasattr(self.storage, 'exists'):
            return self.storage.exists(name)
        
        # Fallback: check MEDIA_ROOT
        path = os.path.join(settings.MEDIA_ROOT, name)
        return os.path.exists(path)
    
    def url(self, name: str) -> str:
        """
        Get the URL for a file.
        
        If name is already a full URL, return it directly.
        Otherwise, construct the URL using the storage backend.
        """
        if not name:
            return ''
        
        # If already a full URL, return it
        if name.startswith(('http://', 'https://')):
            return name
        
        # Use storage backend to get URL
        if hasattr(self.storage, 'get_url'):
            url = self.storage.get_url(name)
            if url:
                return url
        
        # Fallback: construct local URL
        site_url = getattr(settings, 'SITE_URL', '')
        media_url = getattr(settings, 'MEDIA_URL', '/media/')
        
        if site_url:
            return f"{site_url.rstrip('/')}{media_url}{name}"
        return f"{media_url}{name}"
    
    def size(self, name: str) -> int:
        """Get the size of a file."""
        if hasattr(self.storage, 'size'):
            return self.storage.size(name)
        return 0
    
    def listdir(self, path: str):
        """List contents of a directory."""
        if hasattr(self.storage, 'listdir'):
            return self.storage.listdir(path)
        return [], []
    
    def get_accessed_time(self, name: str):
        """Get the last accessed time of a file."""
        return datetime.now()
    
    def get_created_time(self, name: str):
        """Get the creation time of a file."""
        return datetime.now()
    
    def get_modified_time(self, name: str):
        """Get the last modified time of a file."""
        return datetime.now()
    
    def path(self, name: str) -> str:
        """
        Get the local filesystem path for a file.
        Only works for local storage backend.
        """
        # For URLs, there's no local path
        if name.startswith(('http://', 'https://')):
            raise NotImplementedError("Cloud storage files don't have local paths")
        
        # For local storage, return the path
        return os.path.join(settings.MEDIA_ROOT, name)
    
    def generate_filename(self, filename: str) -> str:
        """Generate a unique filename."""
        return filename
    
    def get_valid_name(self, name: str) -> str:
        """Return a valid filename."""
        return name


# Model-specific storage factory
def get_model_storage(model_name: str, field_name: Optional[str] = None) -> DynamicStorage:
    """
    Get a storage instance configured for a specific model.
    
    Checks:
    1. MEDIA_MODEL_BACKENDS setting for model-specific backend
    2. Falls back to default MEDIA_STORAGE_BACKEND
    
    Args:
        model_name: Full model name like 'products.Product'
        field_name: Optional field name for field-specific backend
    
    Returns:
        DynamicStorage instance configured for the model
    """
    model_backends = getattr(settings, 'MEDIA_MODEL_BACKENDS', {})
    backend = model_backends.get(model_name)
    
    if backend:
        logger.debug(f"Using backend '{backend}' for model '{model_name}'")
        return DynamicStorage(backend=backend)
    
    return DynamicStorage()


# Convenience: Create a default instance
default_storage = DynamicStorage()
