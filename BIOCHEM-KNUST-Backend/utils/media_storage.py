"""
Media Storage Utility System

A robust, extensible media upload system that provides a single entry point for all
file/image/video uploads across the entire application. Supports multiple storage
backends (Cloudinary, Google Drive, Local Server, S3, Dropbox, Azure, B2, etc.) with
automatic URL population and load balancing.

This system allows:
1. Easy switching between storage providers
2. Fallback to alternative providers if one fails
3. Automatic URL population in model fields
4. Consistent API across all storage backends
5. URL optimization for different use cases (thumbnails, cards, banners, etc.)
6. Traffic distribution across multiple backends (pool mode)

Usage:
    from utils.media_storage import MediaStorage, get_media_url, upload_media
    
    # Upload a file
    url = upload_media(file_obj, folder='products', filename='image.jpg')
    
    # Get optimized URL
    optimized_url = get_media_url(url, size='card')
    
    # Distributed upload (across multiple providers)
    from utils.media_storage import upload_media_distributed
    result = upload_media_distributed(file_obj, folder='products')

Configuration (in settings.py):
    MEDIA_STORAGE_BACKEND = 'cloudinary'  # or 'local', 'google_drive', 's3', etc.
    MEDIA_STORAGE_FALLBACK = ['local']  # Fallback providers if primary fails
    
    # For distributed uploads:
    MEDIA_STORAGE_POOL = {
        'enabled': True,
        'providers': {
            'cloudinary': {'enabled': True, 'weight': 5},
            's3': {'enabled': True, 'weight': 3},
            'local': {'enabled': True, 'weight': 1},
        },
        'distribution_mode': 'weighted',  # round_robin, weighted, least_used, random
        'fallback_order': ['cloudinary', 's3', 'local'],
    }
"""

import logging
from typing import Optional, Union, Dict, Any, List, BinaryIO

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

# Import all backends from the modular storage_backends package
from .storage_backends import (
    StorageBackend,
    CloudinaryBackend,
    LocalStorageBackend,
    GoogleDriveBackend,
    S3Backend,
    DropboxBackend,
    AzureBlobBackend,
    BackblazeB2Backend,
    MediaStoragePool,
    AVAILABLE_BACKENDS,
)

logger = logging.getLogger(__name__)

# Re-export all backends for backwards compatibility
__all__ = [
    # Base class
    'StorageBackend',
    # Backend implementations
    'CloudinaryBackend',
    'LocalStorageBackend',
    'GoogleDriveBackend',
    'S3Backend',
    'DropboxBackend',
    'AzureBlobBackend',
    'BackblazeB2Backend',
    # Backend registry
    'AVAILABLE_BACKENDS',
    # Pool
    'MediaStoragePool',
    # Manager
    'MediaStorage',
    # Convenience functions
    'upload_media',
    'delete_media',
    'get_media_url',
    'get_thumbnail_url',
    'get_card_url',
    'get_detail_url',
    'get_banner_url',
    'get_avatar_url',
    'extract_url_from_field',
    'get_effective_url',
    'get_media_storage',
    # Pool functions
    'upload_media_distributed',
    'get_pool_stats',
    'enable_storage_provider',
    'disable_storage_provider',
    'get_available_providers',
    'get_enabled_providers',
    'get_storage_pool',
]


# =============================================================================
# MEDIA STORAGE MANAGER (Main Entry Point)
# =============================================================================

class MediaStorage:
    """
    Main media storage manager.
    Provides a unified interface for uploading, retrieving, and managing media files.
    Automatically handles fallback between configured storage providers.
    """
    
    # Registry of available backends (imported from storage_backends package)
    _backends = AVAILABLE_BACKENDS
    
    def __init__(self, backend: Optional[str] = None, fallbacks: Optional[List[str]] = None):
        """
        Initialize MediaStorage with specified or configured backend.
        
        Args:
            backend: Primary storage backend name (default from settings)
            fallbacks: List of fallback backend names (default from settings)
        """
        self.primary_backend_name = backend or getattr(
            settings, 'MEDIA_STORAGE_BACKEND', 'cloudinary'
        )
        self.fallback_names = fallbacks or getattr(
            settings, 'MEDIA_STORAGE_FALLBACK', ['local']
        )
        
        self._primary_backend = None
        self._fallback_backends = []
    
    @classmethod
    def register_backend(cls, name: str, backend_class: type):
        """
        Register a new storage backend.
        
        Example:
            from utils.media_storage import MediaStorage, StorageBackend
            
            class MyCustomBackend(StorageBackend):
                name = "my_custom"
                # ... implement methods
            
            MediaStorage.register_backend('my_custom', MyCustomBackend)
        """
        if not issubclass(backend_class, StorageBackend):
            raise ValueError("Backend must be a subclass of StorageBackend")
        cls._backends[name] = backend_class
    
    def _get_backend(self, name: str) -> Optional[StorageBackend]:
        """Get backend instance by name."""
        if name not in self._backends:
            logger.warning(f"Unknown storage backend: {name}")
            return None
        
        try:
            return self._backends[name]()
        except Exception as e:
            logger.error(f"Failed to initialize backend {name}: {e}")
            return None
    
    @property
    def primary_backend(self) -> Optional[StorageBackend]:
        """Get primary backend instance (lazy loading)."""
        if self._primary_backend is None:
            self._primary_backend = self._get_backend(self.primary_backend_name)
        return self._primary_backend
    
    @property
    def fallback_backends(self) -> List[StorageBackend]:
        """Get fallback backend instances (lazy loading)."""
        if not self._fallback_backends:
            for name in self.fallback_names:
                backend = self._get_backend(name)
                if backend and backend.is_available():
                    self._fallback_backends.append(backend)
        return self._fallback_backends
    
    def upload(
        self,
        file: Union[BinaryIO, UploadedFile, bytes],
        folder: str = "",
        filename: Optional[str] = None,
        resource_type: str = "image",
        use_fallback: bool = True,
        **options
    ) -> Dict[str, Any]:
        """
        Upload a file to storage.
        
        Args:
            file: File to upload
            folder: Folder/directory to store in
            filename: Optional custom filename
            resource_type: Type of resource ('image', 'video', 'raw')
            use_fallback: Try fallback backends if primary fails
            **options: Additional backend-specific options
        
        Returns:
            Dict with upload result including 'url' key
        """
        backends_to_try = []
        
        # Try primary backend first
        if self.primary_backend and self.primary_backend.is_available():
            backends_to_try.append(self.primary_backend)
        
        # Add fallbacks if enabled
        if use_fallback:
            backends_to_try.extend(self.fallback_backends)
        
        if not backends_to_try:
            return {
                'success': False,
                'error': 'No storage backends available',
                'url': None
            }
        
        errors = []
        for backend in backends_to_try:
            result = backend.upload(file, folder, filename, resource_type, **options)
            if result.get('success'):
                logger.info(f"Successfully uploaded to {backend.name}")
                return result
            else:
                errors.append(f"{backend.name}: {result.get('error', 'Unknown error')}")
                logger.warning(f"Upload to {backend.name} failed: {result.get('error')}")
        
        return {
            'success': False,
            'error': f"All backends failed: {'; '.join(errors)}",
            'url': None
        }
    
    def delete(self, public_id: str, resource_type: str = "image") -> bool:
        """Delete a file from storage."""
        if self.primary_backend:
            return self.primary_backend.delete(public_id, resource_type)
        return False
    
    def get_url(
        self,
        identifier: str,
        resource_type: str = "image",
        **transformations
    ) -> Optional[str]:
        """Get URL for a stored file."""
        if self.primary_backend:
            return self.primary_backend.get_url(identifier, resource_type, **transformations)
        return None
    
    def optimize_url(
        self,
        url: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        quality: str = "auto",
        format: str = "auto",
        **options
    ) -> str:
        """
        Optimize URL for faster loading.
        Delegates to the appropriate backend based on URL.
        """
        if not url:
            return url
        
        # Check which backend's URL this is
        if 'cloudinary.com' in url:
            backend = self._get_backend('cloudinary')
            if backend:
                return backend.optimize_url(url, width, height, quality, format, **options)
        
        if 'drive.google.com' in url:
            backend = self._get_backend('google_drive')
            if backend:
                return backend.optimize_url(url, width, height, quality, format)
        
        # Default: try primary backend's optimizer
        if self.primary_backend:
            return self.primary_backend.optimize_url(url, width, height, quality, format, **options)
        
        return url


# =============================================================================
# CONVENIENCE FUNCTIONS (Main API)
# =============================================================================

# Global instance (lazy loaded)
_media_storage: Optional[MediaStorage] = None


def get_media_storage() -> MediaStorage:
    """Get the global MediaStorage instance."""
    global _media_storage
    if _media_storage is None:
        _media_storage = MediaStorage()
    return _media_storage


def upload_media(
    file: Union[BinaryIO, UploadedFile, bytes],
    folder: str = "",
    filename: Optional[str] = None,
    resource_type: str = "image",
    **options
) -> Dict[str, Any]:
    """
    Upload a media file to storage.
    
    This is the main function to use for uploads throughout the application.
    
    Args:
        file: File to upload (file object, uploaded file, or bytes)
        folder: Folder to store the file in (e.g., 'products', 'events')
        filename: Optional custom filename
        resource_type: Type of file ('image', 'video', 'raw')
        **options: Additional backend-specific options
    
    Returns:
        Dict with:
        - success: bool
        - url: str (the accessible URL) or None
        - public_id: str (identifier for deletion)
        - error: str (if failed)
    
    Example:
        from utils.media_storage import upload_media
        
        result = upload_media(request.FILES['image'], folder='products')
        if result['success']:
            product.image_url = result['url']
            product.save()
    """
    return get_media_storage().upload(file, folder, filename, resource_type, **options)


def delete_media(public_id: str, resource_type: str = "image") -> bool:
    """
    Delete a media file from storage.
    
    Args:
        public_id: The identifier returned when uploading
        resource_type: Type of resource
    
    Returns:
        True if deleted successfully
    """
    return get_media_storage().delete(public_id, resource_type)


def get_media_url(
    url_or_identifier: str,
    size: Optional[str] = None,
    width: Optional[int] = None,
    height: Optional[int] = None,
    **options
) -> Optional[str]:
    """
    Get optimized media URL.
    
    Args:
        url_or_identifier: URL or public_id of the media
        size: Preset size ('thumbnail', 'card', 'detail', 'banner', 'avatar')
        width: Custom width (overrides size preset)
        height: Custom height (overrides size preset)
        **options: Additional options (quality, format, crop, etc.)
    
    Returns:
        Optimized URL string
    
    Example:
        from utils.media_storage import get_media_url
        
        # Using preset
        thumb_url = get_media_url(product.image_url, size='thumbnail')
        
        # Using custom dimensions
        custom_url = get_media_url(product.image_url, width=600, height=400)
    """
    if not url_or_identifier:
        return None
    
    # Size presets
    SIZE_PRESETS = {
        'thumbnail': {'width': 100, 'height': 100, 'crop': 'thumb'},
        'avatar': {'width': 150, 'height': 150, 'crop': 'thumb'},
        'card': {'width': 400},
        'detail': {'width': 800},
        'banner': {'width': 1200},
        'full': {},  # No transformation
    }
    
    # Apply size preset if specified
    if size and size in SIZE_PRESETS:
        preset = SIZE_PRESETS[size]
        width = width or preset.get('width')
        height = height or preset.get('height')
        if 'crop' in preset and 'crop' not in options:
            options['crop'] = preset['crop']
    
    storage = get_media_storage()
    return storage.optimize_url(url_or_identifier, width=width, height=height, **options)


# Size-specific convenience functions
def get_thumbnail_url(url: str, size: int = 100) -> Optional[str]:
    """Get thumbnail URL (square crop)."""
    return get_media_url(url, width=size, height=size, crop='thumb')


def get_card_url(url: str, width: int = 400) -> Optional[str]:
    """Get card/list image URL."""
    return get_media_url(url, width=width)


def get_detail_url(url: str, width: int = 800) -> Optional[str]:
    """Get detail view image URL."""
    return get_media_url(url, width=width)


def get_banner_url(url: str, width: int = 1200) -> Optional[str]:
    """Get banner/hero image URL."""
    return get_media_url(url, width=width)


def get_avatar_url(url: str, size: int = 150) -> Optional[str]:
    """Get avatar/profile image URL."""
    return get_media_url(url, width=size, height=size, crop='thumb')


# =============================================================================
# URL EXTRACTION HELPERS
# =============================================================================

def extract_url_from_field(field_value: Any, fallback_url: Optional[str] = None) -> Optional[str]:
    """
    Extract URL from various field types (CloudinaryField, ImageField, URLField, str).
    
    This helper handles the common pattern of having both a file field and URL field.
    
    Args:
        field_value: The field value (could be CloudinaryField, ImageField, str, etc.)
        fallback_url: Fallback URL if field is empty
    
    Returns:
        URL string or None
    """
    if not field_value:
        return fallback_url
    
    # If it's already a string URL
    if isinstance(field_value, str):
        return field_value if field_value else fallback_url
    
    # If it has a .url attribute (CloudinaryField, ImageField, FileField)
    if hasattr(field_value, 'url'):
        try:
            url = field_value.url
            return url if url else fallback_url
        except (ValueError, AttributeError):
            return fallback_url
    
    # If it has a build_url method (Cloudinary)
    if hasattr(field_value, 'build_url'):
        try:
            return field_value.build_url(secure=True)
        except Exception:
            pass
    
    return fallback_url


# Type hint for Any since we don't want heavy imports
try:
    from typing import Any
except ImportError:
    Any = object


def get_effective_url(
    file_field: Any,
    url_field: Optional[str],
    optimize: bool = True,
    size: Optional[str] = None,
    **options
) -> Optional[str]:
    """
    Get the effective URL from a file field and URL field combination.
    
    This is the recommended way to get URLs in serializers and views.
    It handles the priority: uploaded file URL > external URL field.
    
    Args:
        file_field: The file field value (CloudinaryField, ImageField, etc.)
        url_field: The URL field value (URLField string)
        optimize: Whether to optimize the URL
        size: Size preset for optimization
        **options: Additional optimization options
    
    Returns:
        URL string or None
    
    Example:
        # In a serializer
        def get_image_url(self, obj):
            return get_effective_url(
                obj.image,        # CloudinaryField
                obj.image_url,    # URLField
                size='card'
            )
    """
    # Priority: file field (Cloudinary/ImageField) > URL field
    url = extract_url_from_field(file_field) or url_field
    
    if not url:
        return None
    
    if optimize:
        return get_media_url(url, size=size, **options)
    
    return url


# =============================================================================
# STORAGE POOL CONVENIENCE FUNCTIONS
# =============================================================================

# Global pool instance (lazy loaded)
_storage_pool: Optional[MediaStoragePool] = None


def get_storage_pool() -> MediaStoragePool:
    """Get the global MediaStoragePool instance."""
    global _storage_pool
    if _storage_pool is None:
        _storage_pool = MediaStoragePool()
    return _storage_pool


def upload_media_distributed(
    file: Union[BinaryIO, UploadedFile, bytes],
    folder: str = "",
    filename: Optional[str] = None,
    resource_type: str = "image",
    preferred_provider: Optional[str] = None,
    **options
) -> Dict[str, Any]:
    """
    Upload a media file using the storage pool with automatic traffic distribution.
    
    This function distributes uploads across enabled storage providers using
    the configured distribution mode (round-robin, weighted, least-used, random).
    
    Args:
        file: File to upload (file object, uploaded file, or bytes)
        folder: Folder to store the file in (e.g., 'products', 'events')
        filename: Optional custom filename
        resource_type: Type of file ('image', 'video', 'raw')
        preferred_provider: Force a specific provider (bypasses distribution)
        **options: Additional backend-specific options
    
    Returns:
        Dict with:
        - success: bool
        - url: str (the accessible URL) or None
        - public_id: str (identifier for deletion)
        - provider: str (which provider handled the upload)
        - error: str (if failed)
    
    Example:
        from utils.media_storage import upload_media_distributed
        
        # Auto-distribute across enabled providers
        result = upload_media_distributed(request.FILES['image'], folder='products')
        
        # Force specific provider
        result = upload_media_distributed(
            request.FILES['image'],
            folder='products',
            preferred_provider='google_drive'
        )
    """
    return get_storage_pool().upload(
        file, folder, filename, resource_type, preferred_provider, **options
    )


def get_pool_stats() -> Dict[str, Any]:
    """
    Get storage pool usage statistics.
    
    Returns:
        Dict with backend stats and totals
    
    Example:
        from utils.media_storage import get_pool_stats
        
        stats = get_pool_stats()
        print(f"Total uploads: {stats['total_uploads']}")
    """
    return get_storage_pool().get_stats()


def enable_storage_provider(name: str) -> bool:
    """
    Enable a storage provider in the pool.
    
    Args:
        name: Provider name ('cloudinary', 's3', 'dropbox', etc.)
    
    Returns:
        True if enabled successfully
    """
    return get_storage_pool().enable_backend(name)


def disable_storage_provider(name: str) -> bool:
    """
    Disable a storage provider in the pool.
    
    Args:
        name: Provider name ('cloudinary', 's3', 'dropbox', etc.)
    
    Returns:
        True if disabled successfully
    """
    return get_storage_pool().disable_backend(name)


def get_available_providers() -> List[str]:
    """
    Get list of all available storage providers.
    
    Returns:
        List of provider names that are properly configured
    """
    available = []
    for name, backend_class in AVAILABLE_BACKENDS.items():
        try:
            backend = backend_class()
            if backend.is_available():
                available.append(name)
        except Exception:
            pass
    return available


def get_enabled_providers() -> List[str]:
    """
    Get list of currently enabled providers in the pool.
    
    Returns:
        List of enabled provider names
    """
    return get_storage_pool().get_available_backends()
