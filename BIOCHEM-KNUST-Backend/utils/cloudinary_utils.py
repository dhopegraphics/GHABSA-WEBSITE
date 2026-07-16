"""
Cloudinary URL Optimization Utilities

This module provides functions to optimize Cloudinary image URLs for faster loading
on both web and mobile platforms.

NOTE: This module is maintained for backward compatibility. 
For new code, prefer using the generic media_storage module:
    from utils.media_storage import get_media_url, get_thumbnail_url, upload_media

Optimizations include:
- Automatic format conversion (WebP, AVIF when supported)
- Automatic quality compression
- Optional resizing
- HTTPS enforcement (required for iOS)
"""

import re
from typing import Optional

# Import from the generic media storage module for new implementations
from utils.media_storage import (
    upload_media,
    delete_media,
    get_media_url as generic_get_media_url,
    get_effective_url,
    extract_url_from_field,
    MediaStorage,
)


def get_optimized_cloudinary_url(
    url: Optional[str], 
    width: Optional[int] = None, 
    height: Optional[int] = None,
    quality: str = "auto", 
    format: str = "auto",
    crop: Optional[str] = None
) -> Optional[str]:
    """
    Add Cloudinary transformations to optimize image loading.
    
    Args:
        url: The original Cloudinary image URL
        width: Target width in pixels (maintains aspect ratio if height not set)
        height: Target height in pixels
        quality: Quality setting - 'auto', 'auto:low', 'auto:eco', 'auto:good', 'auto:best', or 1-100
        format: Format setting - 'auto' (recommended), 'webp', 'avif', 'jpg', 'png'
        crop: Crop mode - 'fill', 'fit', 'scale', 'thumb', 'limit' etc.
    
    Returns:
        Optimized URL string or None if input is None/empty
    
    Examples:
        # Basic optimization (auto format + quality)
        get_optimized_cloudinary_url(url)
        
        # With width resize
        get_optimized_cloudinary_url(url, width=400)
        
        # Thumbnail with crop
        get_optimized_cloudinary_url(url, width=100, height=100, crop='thumb')
    """
    if not url:
        return None
    
    # Ensure HTTPS (iOS blocks HTTP by default)
    if url.startswith('http://'):
        url = url.replace('http://', 'https://', 1)
    
    # Check if it's a Cloudinary URL
    if 'cloudinary.com' not in url:
        return url
    
    # Build transformation string
    transformations = [f"f_{format}", f"q_{quality}"]
    
    if width:
        transformations.append(f"w_{width}")
    if height:
        transformations.append(f"h_{height}")
    if crop:
        transformations.append(f"c_{crop}")
    
    transform_str = ",".join(transformations)
    
    # Check if transformations already exist
    if '/upload/f_' in url or '/upload/q_' in url or '/upload/w_' in url:
        return url  # Already has transformations
    
    # Insert transformations into URL
    # Cloudinary URL format: .../upload/[transformations]/...
    pattern = r'(/upload/)([^/])'
    replacement = rf'\1{transform_str}/\2'
    
    optimized_url = re.sub(pattern, replacement, url)
    return optimized_url


def get_thumbnail_url(url: Optional[str], size: int = 100) -> Optional[str]:
    """
    Generate a thumbnail URL for the image.
    
    Args:
        url: The original Cloudinary image URL
        size: Thumbnail size (square, in pixels)
    
    Returns:
        Optimized thumbnail URL
    """
    return get_optimized_cloudinary_url(url, width=size, height=size, crop='thumb')


def get_card_image_url(url: Optional[str], width: int = 400) -> Optional[str]:
    """
    Generate an optimized URL for card/list view images.
    
    Args:
        url: The original Cloudinary image URL
        width: Target width (default 400px for mobile cards)
    
    Returns:
        Optimized URL for card display
    """
    return get_optimized_cloudinary_url(url, width=width)


def get_detail_image_url(url: Optional[str], width: int = 800) -> Optional[str]:
    """
    Generate an optimized URL for detail/full view images.
    
    Args:
        url: The original Cloudinary image URL
        width: Target width (default 800px for detail views)
    
    Returns:
        Optimized URL for detail display
    """
    return get_optimized_cloudinary_url(url, width=width)


def get_banner_image_url(url: Optional[str], width: int = 1200) -> Optional[str]:
    """
    Generate an optimized URL for banner/hero images.
    
    Args:
        url: The original Cloudinary image URL
        width: Target width (default 1200px for banners)
    
    Returns:
        Optimized URL for banner display
    """
    return get_optimized_cloudinary_url(url, width=width)


def get_avatar_url(url: Optional[str], size: int = 150) -> Optional[str]:
    """
    Generate an optimized URL for avatar/profile images.
    
    Args:
        url: The original Cloudinary image URL
        size: Avatar size (square, in pixels)
    
    Returns:
        Optimized avatar URL
    """
    return get_optimized_cloudinary_url(url, width=size, height=size, crop='thumb')


# =============================================================================
# GENERIC MEDIA UPLOAD FUNCTIONS (Provider-agnostic)
# =============================================================================
# These functions use the new generic media storage system that supports
# multiple backends (Cloudinary, Local, S3, Google Drive, etc.)

def upload_image(file, folder: str = "", filename: Optional[str] = None, **options) -> dict:
    """
    Upload an image using the configured storage backend.
    
    This is a convenience wrapper around upload_media that defaults to image type.
    
    Args:
        file: File object, uploaded file, or bytes to upload
        folder: Folder to store the image in (e.g., 'products', 'events')
        filename: Optional custom filename
        **options: Additional backend-specific options
    
    Returns:
        Dict with 'success', 'url', 'public_id', 'error' keys
    
    Example:
        result = upload_image(request.FILES['image'], folder='products')
        if result['success']:
            product.image_url = result['url']
            product.save()
    """
    return upload_media(file, folder=folder, filename=filename, resource_type='image', **options)


def upload_video(file, folder: str = "", filename: Optional[str] = None, **options) -> dict:
    """
    Upload a video using the configured storage backend.
    
    Args:
        file: File object, uploaded file, or bytes to upload
        folder: Folder to store the video in
        filename: Optional custom filename
        **options: Additional backend-specific options
    
    Returns:
        Dict with 'success', 'url', 'public_id', 'error' keys
    """
    return upload_media(file, folder=folder, filename=filename, resource_type='video', **options)


def upload_file(file, folder: str = "", filename: Optional[str] = None, **options) -> dict:
    """
    Upload a raw file (PDF, document, etc.) using the configured storage backend.
    
    Args:
        file: File object, uploaded file, or bytes to upload
        folder: Folder to store the file in
        filename: Optional custom filename
        **options: Additional backend-specific options
    
    Returns:
        Dict with 'success', 'url', 'public_id', 'error' keys
    """
    return upload_media(file, folder=folder, filename=filename, resource_type='raw', **options)


def delete_uploaded_file(public_id: str, resource_type: str = "image") -> bool:
    """
    Delete a previously uploaded file.
    
    Args:
        public_id: The identifier returned from upload
        resource_type: Type of resource ('image', 'video', 'raw')
    
    Returns:
        True if deleted successfully
    """
    return delete_media(public_id, resource_type)


# =============================================================================
# UTILITY FUNCTIONS FOR MODELS AND SERIALIZERS
# =============================================================================

def get_url_from_field(field_value, fallback_url: Optional[str] = None) -> Optional[str]:
    """
    Extract URL from various field types (CloudinaryField, ImageField, URLField, str).
    
    This is the preferred way to get URLs in serializers and views.
    
    Args:
        field_value: The field value (could be CloudinaryField, ImageField, str, etc.)
        fallback_url: Fallback URL if field is empty
    
    Returns:
        URL string or None
    
    Example:
        def get_image_url(self, obj):
            return get_url_from_field(obj.image, obj.image_url)
    """
    return extract_url_from_field(field_value, fallback_url)


def get_best_url(file_field, url_field: Optional[str], size: Optional[str] = None, **options) -> Optional[str]:
    """
    Get the best available URL from a file field and URL field combination.
    
    Priority: uploaded file URL > external URL field.
    Optionally applies size optimization.
    
    Args:
        file_field: The file field value (CloudinaryField, ImageField, etc.)
        url_field: The URL field value (URLField string)
        size: Size preset for optimization ('thumbnail', 'card', 'detail', 'banner', 'avatar')
        **options: Additional optimization options
    
    Returns:
        URL string or None
    
    Example:
        # In a serializer
        def get_image_url(self, obj):
            return get_best_url(obj.product_image, obj.product_image_url, size='card')
    """
    return get_effective_url(file_field, url_field, optimize=True, size=size, **options)


# Re-export everything from media_storage for convenience
__all__ = [
    # Legacy Cloudinary functions (still work, provider-specific)
    'get_optimized_cloudinary_url',
    'get_thumbnail_url',
    'get_card_image_url',
    'get_detail_image_url',
    'get_banner_image_url',
    'get_avatar_url',
    
    # Generic upload functions (provider-agnostic, use these for new code)
    'upload_image',
    'upload_video',
    'upload_file',
    'upload_media',
    'delete_uploaded_file',
    'delete_media',
    
    # URL handling functions
    'get_url_from_field',
    'get_best_url',
    'get_effective_url',
    'extract_url_from_field',
    'generic_get_media_url',
    
    # Main class for advanced usage
    'MediaStorage',
]
