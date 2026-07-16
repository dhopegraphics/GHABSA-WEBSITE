"""
Storage Backend Base Class

Abstract base class that all storage backends must implement.
This defines the common interface for uploading, deleting, and retrieving media files.
"""

import logging
from abc import ABC, abstractmethod
from typing import Optional, Union, Dict, Any, BinaryIO

from django.core.files.uploadedfile import UploadedFile

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """
    Abstract base class for all storage backends.
    Each storage provider (Cloudinary, S3, Local, etc.) must implement this interface.
    
    To create a new backend:
    1. Create a new file in storage_backends/ (e.g., my_backend.py)
    2. Create a class that inherits from StorageBackend
    3. Implement all abstract methods
    4. Register it in __init__.py and AVAILABLE_BACKENDS
    
    Example:
        class MyBackend(StorageBackend):
            name = "my_backend"
            
            def is_available(self) -> bool:
                return bool(getattr(settings, 'MY_BACKEND_KEY', None))
            
            def upload(self, file, folder="", filename=None, resource_type="image", **options):
                # Upload logic here
                return {'success': True, 'url': '...', 'public_id': '...'}
            
            def delete(self, public_id, resource_type="image") -> bool:
                # Delete logic here
                return True
            
            def get_url(self, identifier, resource_type="image", **transformations):
                return f"https://.../{identifier}"
    """
    
    name: str = "base"
    
    @abstractmethod
    def upload(
        self,
        file: Union[BinaryIO, UploadedFile, bytes],
        folder: str = "",
        filename: Optional[str] = None,
        resource_type: str = "image",
        **options
    ) -> Dict[str, Any]:
        """
        Upload a file to the storage backend.
        
        Args:
            file: File object, uploaded file, or bytes to upload
            folder: Folder/directory to store the file in
            filename: Optional custom filename
            resource_type: Type of resource ('image', 'video', 'raw')
            **options: Additional provider-specific options
        
        Returns:
            Dict with at least:
            {
                'success': bool,
                'url': str (the accessible URL),
                'public_id': str (identifier for deletion/reference),
                'resource_type': str,
                'format': str,
                'size': int (bytes),
                'provider': str,
                'error': str (if success is False)
            }
        """
        pass
    
    @abstractmethod
    def delete(self, public_id: str, resource_type: str = "image") -> bool:
        """
        Delete a file from storage.
        
        Args:
            public_id: The identifier of the file to delete
            resource_type: Type of resource
        
        Returns:
            True if deleted successfully, False otherwise
        """
        pass
    
    @abstractmethod
    def get_url(
        self,
        identifier: str,
        resource_type: str = "image",
        **transformations
    ) -> Optional[str]:
        """
        Get URL for a stored file with optional transformations.
        
        Args:
            identifier: File identifier (public_id or URL)
            resource_type: Type of resource
            **transformations: Provider-specific transformations (resize, format, etc.)
        
        Returns:
            URL string or None
        """
        pass
    
    def is_available(self) -> bool:
        """
        Check if this storage backend is configured and available.
        Override in subclasses to check for required settings.
        """
        return True
    
    def optimize_url(
        self,
        url: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        quality: str = "auto",
        format: str = "auto"
    ) -> str:
        """
        Optimize a URL for faster loading (if supported by the backend).
        Default implementation returns URL unchanged.
        
        Args:
            url: Original URL
            width: Target width
            height: Target height
            quality: Quality setting ('auto', 'low', 'medium', 'high')
            format: Output format ('auto', 'webp', 'jpg', 'png')
        
        Returns:
            Optimized URL (or original if optimization not supported)
        """
        return url
