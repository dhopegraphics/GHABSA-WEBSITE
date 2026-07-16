"""
Enhanced Media Field Mixins for Django Models

This module provides automatic:
1. URL population when a file is uploaded (to CloudinaryField, ImageField, etc.)
2. Old file deletion when a file is replaced or cleared
3. File change tracking to detect modifications
4. Model-specific and field-specific storage backend selection

Basic Usage:
    from utils.media_mixins import MediaUrlMixin
    
    class Product(MediaUrlMixin, models.Model):
        product_image = CloudinaryField('image', null=True, blank=True)
        product_image_url = models.URLField(blank=True, null=True)
        
        MEDIA_URL_FIELDS = {
            'product_image': 'product_image_url',
        }

Model-Specific Storage Backend:
    class Product(MediaUrlMixin, models.Model):
        # All uploads for this model will use Google Drive
        MEDIA_STORAGE_BACKEND = 'google_drive'
        
        MEDIA_URL_FIELDS = {
            'product_image': 'product_image_url',
        }
        
        product_image = models.ImageField(upload_to='products/')
        product_image_url = models.URLField(blank=True, null=True)

Field-Specific Storage Backend (Advanced):
    class Product(MediaUrlMixin, models.Model):
        MEDIA_URL_FIELDS = {
            # Simple format: field -> url_field
            'thumbnail': 'thumbnail_url',
            # Advanced format: field -> config dict
            'product_image': {
                'url_field': 'product_image_url',
                'backend': 'google_drive',
                'folder': 'products/images',  # Custom folder
            },
            'product_video': {
                'url_field': 'product_video_url',
                'backend': 's3',
                'resource_type': 'video',
            },
        }

Available Storage Backends:
    - 'local': Local file system storage
    - 'cloudinary': Cloudinary cloud storage
    - 'google_drive': Google Drive storage
    - 's3': Amazon S3 storage
    - 'dropbox': Dropbox storage
    - 'azure_blob': Azure Blob storage
    - 'backblaze_b2': Backblaze B2 storage

When a file is uploaded via Django admin:
- The URL is automatically extracted and saved to the URL field
- If replacing an existing file, the old file is deleted from storage
- If a custom backend is specified, the file is uploaded to that backend

When a file is cleared:
- The old file is deleted from storage
- The URL field is cleared (unless manually set to external URL)
"""

import logging
import re
from typing import Dict, Optional, Any, Type, List, Tuple
from django.db import models
from django.db.models.signals import post_init, pre_save, post_save, post_delete
from django.dispatch import receiver

logger = logging.getLogger(__name__)


def extract_url_from_file_field(field_value: Any) -> Optional[str]:
    """
    Extract URL from various file field types.
    
    Args:
        field_value: Value from a file field (CloudinaryField, ImageField, FileField, etc.)
    
    Returns:
        URL string or None
    """
    if not field_value:
        return None
    
    # If it's already a string (URL)
    if isinstance(field_value, str):
        return field_value if field_value else None
    
    # CloudinaryField, ImageField, FileField all have a .url attribute
    if hasattr(field_value, 'url'):
        try:
            url = field_value.url
            if url:
                # Ensure HTTPS for Cloudinary
                if url.startswith('http://res.cloudinary.com'):
                    url = url.replace('http://', 'https://', 1)
                return url
        except (ValueError, AttributeError):
            pass
    
    # Cloudinary resource might have build_url method
    if hasattr(field_value, 'build_url'):
        try:
            return field_value.build_url(secure=True)
        except Exception:
            pass
    
    return None


def extract_public_id_from_url(url: str) -> Optional[str]:
    """
    Extract public_id/identifier from various cloud storage URLs.
    
    Args:
        url: The cloud storage URL
    
    Returns:
        The public_id/identifier for the cloud provider, or None
    """
    if not url or not isinstance(url, str):
        return None
    
    # Cloudinary URL
    # Format: https://res.cloudinary.com/<cloud_name>/image/upload/v<version>/<public_id>.<format>
    if 'cloudinary.com' in url:
        match = re.search(r'/upload/(?:v\d+/)?(.+?)(?:\.[a-z]+)?$', url)
        if match:
            return match.group(1)
    
    # Google Drive URL
    # Format: https://drive.google.com/file/d/<file_id>/view or https://drive.google.com/uc?id=<file_id>
    if 'drive.google.com' in url:
        match = re.search(r'/d/([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
        match = re.search(r'id=([a-zA-Z0-9_-]+)', url)
        if match:
            return match.group(1)
    
    # Amazon S3 URL
    # Format: https://<bucket>.s3.<region>.amazonaws.com/<key> or https://s3.<region>.amazonaws.com/<bucket>/<key>
    if 's3.amazonaws.com' in url or '.s3.' in url:
        # Try bucket-style URL first
        match = re.search(r's3\.[\w-]+\.amazonaws\.com/(.+)$', url)
        if match:
            return match.group(1)
        # Try path-style URL
        match = re.search(r's3\.amazonaws\.com/[^/]+/(.+)$', url)
        if match:
            return match.group(1)
    
    # Dropbox URL
    # Format: https://www.dropbox.com/s/<id>/<filename> or https://dl.dropboxusercontent.com/...
    if 'dropbox.com' in url or 'dropboxusercontent.com' in url:
        match = re.search(r'/s/([a-zA-Z0-9]+)/', url)
        if match:
            return match.group(1)
        # For direct download links, extract the path
        match = re.search(r'dropboxusercontent\.com/(.+?)(?:\?|$)', url)
        if match:
            return match.group(1)
    
    # Azure Blob URL
    # Format: https://<account>.blob.core.windows.net/<container>/<blob>
    if 'blob.core.windows.net' in url:
        match = re.search(r'blob\.core\.windows\.net/[^/]+/(.+?)(?:\?|$)', url)
        if match:
            return match.group(1)
    
    # Backblaze B2 URL
    # Format: https://f<num>.backblazeb2.com/file/<bucket>/<filename>
    if 'backblazeb2.com' in url or 'b2.' in url:
        match = re.search(r'/file/[^/]+/(.+?)(?:\?|$)', url)
        if match:
            return match.group(1)
    
    return None


def get_public_id_from_field(field_value: Any) -> Optional[str]:
    """
    Extract public_id from a file field for deletion purposes.
    Works with both local and cloud storage files.
    
    Args:
        field_value: Value from a file field
    
    Returns:
        Public ID string or None
    """
    if not field_value:
        return None
    
    # CloudinaryField stores public_id directly
    if hasattr(field_value, 'public_id') and field_value.public_id:
        return field_value.public_id
    
    # Get the name (which could be a path or URL)
    name = None
    if hasattr(field_value, 'name') and field_value.name:
        name = field_value.name
    elif isinstance(field_value, str):
        name = field_value
    
    if not name:
        return None
    
    # If name is a cloud URL, extract the public_id from it
    if name.startswith(('http://', 'https://')):
        extracted = extract_public_id_from_url(name)
        if extracted:
            return extracted
        # If we couldn't extract, return the full URL as fallback
        # (some backends might accept URLs directly)
        return name
    
    # For local storage, return the relative path as the identifier
    return name


def delete_file_from_storage(field_value: Any, public_id: Optional[str] = None, url: Optional[str] = None) -> bool:
    """
    Delete a file from its storage backend.
    Automatically detects which storage backend to use based on URL patterns.
    
    Args:
        field_value: The file field value
        public_id: Optional explicit public_id
        url: Optional URL to help determine storage backend
    
    Returns:
        True if deleted successfully
    """
    if not field_value and not public_id and not url:
        return False
    
    # Get public_id if not provided
    if not public_id:
        public_id = get_public_id_from_field(field_value)
    
    # Get URL for backend detection
    if not url and field_value:
        url = extract_url_from_file_field(field_value)
    
    if not public_id:
        return False
    
    # Detect storage backend from URL
    backend_type = None
    if url:
        if 'cloudinary.com' in url:
            backend_type = 'cloudinary'
        elif 'drive.google.com' in url:
            backend_type = 'google_drive'
        elif 's3.amazonaws.com' in url or '.s3.' in url:
            backend_type = 's3'
        elif 'dropbox.com' in url:
            backend_type = 'dropbox'
        elif 'blob.core.windows.net' in url:
            backend_type = 'azure_blob'
        elif 'backblazeb2.com' in url or 'b2.' in url:
            backend_type = 'backblaze_b2'
    
    # Try Cloudinary if detected or field has Cloudinary attributes
    if backend_type == 'cloudinary' or hasattr(field_value, 'public_id'):
        try:
            import cloudinary.uploader
            result = cloudinary.uploader.destroy(public_id)
            if result.get('result') == 'ok':
                logger.info(f"Deleted file from Cloudinary: {public_id}")
                return True
            else:
                logger.warning(f"Cloudinary deletion returned: {result}")
        except ImportError:
            pass
        except Exception as e:
            logger.error(f"Error deleting from Cloudinary: {e}")
    
    # Try local file deletion if field has path
    try:
        if hasattr(field_value, 'path'):
            import os
            path = field_value.path
            if os.path.exists(path):
                os.remove(path)
                logger.info(f"Deleted local file: {path}")
                return True
    except Exception as e:
        logger.error(f"Error deleting local file: {e}")
    
    # Try using media storage system (handles all backends)
    try:
        from utils.media_storage import AVAILABLE_BACKENDS
        
        # If we know the backend type, use it directly
        if backend_type and backend_type in AVAILABLE_BACKENDS:
            backend_class = AVAILABLE_BACKENDS[backend_type]
            backend = backend_class()
            if backend.is_available() and backend.delete(public_id):
                logger.info(f"Deleted file from {backend_type}: {public_id}")
                return True
        
        # Otherwise try all available backends
        for name, backend_class in AVAILABLE_BACKENDS.items():
            try:
                backend = backend_class()
                if backend.is_available() and backend.delete(public_id):
                    logger.info(f"Deleted file from {name}: {public_id}")
                    return True
            except Exception:
                continue
                
    except Exception as e:
        logger.error(f"Error deleting via media storage: {e}")
    
    logger.warning(f"Could not delete file: {public_id}")
    return False


class MediaUrlMixin(models.Model):
    """
    Enhanced mixin that automatically:
    1. Populates URL fields from file fields when saved
    2. Deletes old files when replaced or cleared
    3. Tracks file changes between saves
    4. Supports model-specific and field-specific storage backends
    
    Basic Usage:
        class Product(MediaUrlMixin, models.Model):
            MEDIA_URL_FIELDS = {
                'product_image': 'product_image_url',
            }
            
            product_image = CloudinaryField('image', null=True, blank=True)
            product_image_url = models.URLField(blank=True, null=True)
    
    Model-Specific Storage Backend:
        class Product(MediaUrlMixin, models.Model):
            MEDIA_URL_FIELDS = {
                'product_image': 'product_image_url',
            }
            # All uploads for this model will use Google Drive
            MEDIA_STORAGE_BACKEND = 'google_drive'
    
    Field-Specific Storage Backend (Advanced):
        class Product(MediaUrlMixin, models.Model):
            MEDIA_URL_FIELDS = {
                # Simple: field -> url_field
                'thumbnail': 'thumbnail_url',
                # Advanced: field -> config dict
                'product_image': {
                    'url_field': 'product_image_url',
                    'backend': 'google_drive',
                    'folder': 'products/images',  # Custom folder
                },
                'product_video': {
                    'url_field': 'product_video_url',
                    'backend': 's3',
                    'resource_type': 'video',
                },
            }
    
    Features:
    - When you upload a file, the URL is automatically saved to the URL field
    - When you replace a file, the old file is deleted from storage
    - When you clear a file, the old file is deleted from storage
    - URL field is cleared when file is cleared (unless it's an external URL)
    - Model-level storage backend override with MEDIA_STORAGE_BACKEND
    - Per-field storage backend override in MEDIA_URL_FIELDS config
    """
    
    # Override this in your model - can be simple or advanced format
    MEDIA_URL_FIELDS: Dict[str, Any] = {}
    
    # Override this to use a specific storage backend for all fields in this model
    # Options: 'local', 'cloudinary', 'google_drive', 's3', 'dropbox', 'azure_blob', 'backblaze_b2'
    MEDIA_STORAGE_BACKEND: Optional[str] = None
    
    class Meta:
        abstract = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Store original file values to detect changes
        self._original_files = {}
        self._store_original_files()
    
    def _get_field_config(self, file_field_name: str) -> Dict[str, Any]:
        """
        Get the configuration for a file field.
        
        Priority for backend selection:
        1. Field-level backend (in MEDIA_URL_FIELDS dict config)
        2. Model-level backend (MEDIA_STORAGE_BACKEND class attribute)
        3. Settings-level model backend (MEDIA_MODEL_BACKENDS setting)
        4. Default backend (from MEDIA_STORAGE_BACKEND setting)
        
        Returns a normalized config dict with:
        - url_field: str (the URL field name)
        - backend: str or None (storage backend to use)
        - folder: str or None (custom folder)
        - resource_type: str (image, video, raw)
        """
        from django.conf import settings
        
        config = self.MEDIA_URL_FIELDS.get(file_field_name, {})
        
        # Determine backend with priority
        model_key = f"{self._meta.app_label}.{self.__class__.__name__}"
        settings_backend = getattr(settings, 'MEDIA_MODEL_BACKENDS', {}).get(model_key)
        
        # Simple format: just the URL field name as string
        if isinstance(config, str):
            # Priority: class attribute > settings > None (use default)
            backend = self.MEDIA_STORAGE_BACKEND or settings_backend
            return {
                'url_field': config,
                'backend': backend,
                'folder': None,
                'resource_type': 'image',
            }
        
        # Advanced format: dict with configuration
        # Field-level backend has highest priority
        field_backend = config.get('backend')
        backend = field_backend or self.MEDIA_STORAGE_BACKEND or settings_backend
        
        return {
            'url_field': config.get('url_field', f'{file_field_name}_url'),
            'backend': backend,
            'folder': config.get('folder'),
            'resource_type': config.get('resource_type', 'image'),
        }
    
    def _get_storage_backend(self, backend_name: Optional[str] = None):
        """
        Get the storage backend instance for uploading.
        
        Args:
            backend_name: Specific backend to use, or None for default
        
        Returns:
            Storage backend instance
        """
        try:
            from utils.media_storage import AVAILABLE_BACKENDS, get_media_storage
            
            # If specific backend requested
            if backend_name and backend_name in AVAILABLE_BACKENDS:
                backend_class = AVAILABLE_BACKENDS[backend_name]
                backend = backend_class()
                if backend.is_available():
                    logger.info(f"Using storage backend: {backend_name}")
                    return backend
                else:
                    logger.warning(f"Requested backend '{backend_name}' is not available, falling back to default")
            
            # Fall back to default MediaStorage
            return get_media_storage()
            
        except Exception as e:
            logger.error(f"Error getting storage backend: {e}")
            return None
    
    def _upload_file_to_backend(self, file_obj, config: Dict[str, Any]) -> Optional[str]:
        """
        Upload a file using the specified backend configuration.
        
        Args:
            file_obj: The file to upload
            config: Field configuration dict
        
        Returns:
            URL string or None
        """
        if not file_obj:
            return None
            
        try:
            backend = self._get_storage_backend(config.get('backend'))
            if not backend:
                return None
            
            # Determine folder
            folder = config.get('folder')
            if not folder:
                # Auto-generate folder based on model and field
                app_label = self._meta.app_label
                model_name = self.__class__.__name__
                folder = f"{app_label}/{model_name}"
            
            # Get filename from file object
            filename = None
            if hasattr(file_obj, 'name'):
                filename = file_obj.name
            
            # Upload using the backend
            if hasattr(backend, 'upload'):
                result = backend.upload(
                    file_obj,
                    folder=folder,
                    filename=filename,
                    resource_type=config.get('resource_type', 'image'),
                )
                if result.get('success'):
                    url = result.get('url')
                    logger.info(f"Uploaded file to {config.get('backend', 'default')}: {url}")
                    return url
                else:
                    logger.error(f"Upload failed: {result.get('error')}")
            
        except Exception as e:
            logger.error(f"Error uploading file: {e}")
        
        return None
    
    def _store_original_files(self):
        """Store the original file values for change detection."""
        for file_field_name in self.MEDIA_URL_FIELDS.keys():
            try:
                field_value = getattr(self, file_field_name, None)
                # Store the public_id or name for comparison
                if field_value:
                    self._original_files[file_field_name] = get_public_id_from_field(field_value)
                else:
                    self._original_files[file_field_name] = None
            except Exception:
                self._original_files[file_field_name] = None
    
    def _get_file_changed(self, file_field_name: str) -> Tuple[bool, Optional[str]]:
        """
        Check if a file field has changed.
        
        Returns:
            Tuple of (has_changed, old_public_id)
        """
        original_id = self._original_files.get(file_field_name)
        current_value = getattr(self, file_field_name, None)
        current_id = get_public_id_from_field(current_value)
        
        # File changed if IDs are different
        if original_id != current_id:
            return True, original_id
        
        return False, None
    
    def _sync_media_urls_and_cleanup(self):
        """
        Sync URL fields with file fields and delete old files if changed.
        Now supports model-specific and field-specific storage backends.
        """
        for file_field_name in self.MEDIA_URL_FIELDS.keys():
            try:
                # Get field configuration (supports both simple and advanced formats)
                config = self._get_field_config(file_field_name)
                url_field_name = config['url_field']
                
                # Check if file changed
                has_changed, old_public_id = self._get_file_changed(file_field_name)
                
                current_file = getattr(self, file_field_name, None)
                current_url = getattr(self, url_field_name, None)
                
                # Extract URL from current file
                extracted_url = extract_url_from_file_field(current_file)
                
                # Check if this is a new file upload that needs to go to a specific backend
                file_needs_upload = False
                if has_changed and current_file and config.get('backend'):
                    # Check if the file was just uploaded (has a file but URL isn't from the target backend)
                    if hasattr(current_file, 'file') and hasattr(current_file.file, 'read'):
                        file_needs_upload = True
                
                if has_changed:
                    logger.info(f"File field '{file_field_name}' changed on {self.__class__.__name__}")
                    
                    # Delete old file if it existed
                    if old_public_id:
                        logger.info(f"Deleting old file: {old_public_id}")
                        delete_file_from_storage(None, old_public_id)
                    
                    # Upload to specific backend if configured
                    if file_needs_upload:
                        logger.info(f"Uploading to backend: {config.get('backend')}")
                        uploaded_url = self._upload_file_to_backend(current_file, config)
                        if uploaded_url:
                            setattr(self, url_field_name, uploaded_url)
                            logger.info(f"Set {url_field_name} = {uploaded_url} (from {config.get('backend')})")
                            continue  # Skip the rest, upload handled
                    
                    # Update URL field (default behavior)
                    if extracted_url:
                        # New file uploaded - set URL
                        setattr(self, url_field_name, extracted_url)
                        logger.info(f"Set {url_field_name} = {extracted_url}")
                    else:
                        # File cleared - check if URL was from file or external
                        if current_url and old_public_id:
                            # URL was from file, clear it
                            # Check if current URL contains the old public_id
                            if old_public_id in str(current_url):
                                setattr(self, url_field_name, None)
                                logger.info(f"Cleared {url_field_name} (file was cleared)")
                else:
                    # File didn't change, but maybe URL needs initial population
                    if extracted_url and not current_url:
                        setattr(self, url_field_name, extracted_url)
                        logger.info(f"Initial population: {url_field_name} = {extracted_url}")
                    elif extracted_url and current_url:
                        # Both exist - update URL to match file (in case file has new URL format)
                        # Only update if the URL is from the same storage
                        if self._is_same_storage(extracted_url, current_url):
                            setattr(self, url_field_name, extracted_url)
                
            except Exception as e:
                logger.error(f"Error syncing {file_field_name} -> {url_field_name}: {e}")
    
    def _is_same_storage(self, url1: str, url2: str) -> bool:
        """Check if two URLs are from the same storage provider."""
        if not url1 or not url2:
            return False
        
        # Check for common patterns
        providers = ['cloudinary.com', 'drive.google.com', 's3.amazonaws.com', 
                    'blob.core.windows.net', 'dropbox.com', 'backblazeb2.com']
        
        for provider in providers:
            if provider in url1 and provider in url2:
                return True
        
        return False
    
    def save(self, *args, **kwargs):
        """Override save to auto-populate URLs and cleanup old files."""
        self._sync_media_urls_and_cleanup()
        super().save(*args, **kwargs)
        # Update original files after save
        self._store_original_files()
    
    def refresh_from_db(self, *args, **kwargs):
        """Override to update original files cache after refresh."""
        super().refresh_from_db(*args, **kwargs)
        self._store_original_files()

    def delete(self, *args, **kwargs):
        """
        Override delete to cleanup all media files when the model instance is deleted.
        This prevents orphaned files from accumulating in storage.
        
        IMPORTANT: Only deletes files that were actually UPLOADED through our system.
        External URLs (Google Drive links, Dropbox links, etc.) that users manually 
        entered into the _url fields are NOT affected - those are just database entries.
        """
        for file_field_name in self.MEDIA_URL_FIELDS.keys():
            try:
                file_value = getattr(self, file_field_name, None)
                
                # Only proceed if there's an actual uploaded file (not just a URL)
                # file_value will be a FieldFile object if uploaded, None/empty otherwise
                if file_value and hasattr(file_value, 'name') and file_value.name:
                    public_id = get_public_id_from_field(file_value)
                    if public_id:
                        logger.info(f"Deleting uploaded file on model delete: {public_id}")
                        delete_file_from_storage(file_value, public_id)
                    else:
                        logger.debug(f"No public_id found for {file_field_name}, skipping deletion")
                else:
                    logger.debug(f"No uploaded file in {file_field_name}, skipping deletion (may be external URL only)")
            except Exception as e:
                logger.error(f"Error deleting file '{file_field_name}' on model delete: {e}")
        
        super().delete(*args, **kwargs)


class MediaCleanupMixin(models.Model):
    """
    Mixin that only handles file cleanup (deletion) when files are removed.
    Use this if you don't want automatic URL population but want cleanup.
    
    Usage:
        class Document(MediaCleanupMixin, models.Model):
            MEDIA_FILE_FIELDS = ['document', 'attachment']
            
            document = models.FileField(upload_to='documents/')
            attachment = models.FileField(upload_to='attachments/')
    """
    
    MEDIA_FILE_FIELDS: List[str] = []
    
    class Meta:
        abstract = True
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._original_files = {}
        self._store_original_files()
    
    def _store_original_files(self):
        """Store original file values."""
        for field_name in self.MEDIA_FILE_FIELDS:
            try:
                field_value = getattr(self, field_name, None)
                if field_value:
                    self._original_files[field_name] = get_public_id_from_field(field_value)
                else:
                    self._original_files[field_name] = None
            except Exception:
                self._original_files[field_name] = None
    
    def _cleanup_old_files(self):
        """Delete old files that were replaced or cleared."""
        for field_name in self.MEDIA_FILE_FIELDS:
            original_id = self._original_files.get(field_name)
            current_value = getattr(self, field_name, None)
            current_id = get_public_id_from_field(current_value)
            
            if original_id and original_id != current_id:
                logger.info(f"Cleaning up old file: {original_id}")
                delete_file_from_storage(None, original_id)
    
    def save(self, *args, **kwargs):
        """Override save to cleanup old files."""
        self._cleanup_old_files()
        super().save(*args, **kwargs)
        self._store_original_files()
    
    def delete(self, *args, **kwargs):
        """
        Override delete to cleanup all uploaded files.
        Only deletes files that were actually uploaded, not external URLs.
        """
        for field_name in self.MEDIA_FILE_FIELDS:
            field_value = getattr(self, field_name, None)
            # Only proceed if there's an actual uploaded file
            if field_value and hasattr(field_value, 'name') and field_value.name:
                public_id = get_public_id_from_field(field_value)
                if public_id:
                    logger.info(f"Deleting uploaded file on model delete: {public_id}")
                    delete_file_from_storage(field_value, public_id)
        
        super().delete(*args, **kwargs)


# =============================================================================
# DJANGO ADMIN INTEGRATION
# =============================================================================

def make_media_admin_mixin(file_field_names: List[str]):
    """
    Create an admin mixin that handles file cleanup on admin actions.
    
    IMPORTANT: Only deletes files that were actually UPLOADED through our system.
    External URLs (Google Drive links, Dropbox links, etc.) that users manually 
    entered into the _url fields are NOT affected.
    
    Usage:
        ProductAdminMixin = make_media_admin_mixin(['product_image'])
        
        @admin.register(Product)
        class ProductAdmin(ProductAdminMixin, admin.ModelAdmin):
            ...
    """
    class MediaAdminMixin:
        def save_model(self, request, obj, form, change):
            """Override to handle file changes in admin."""
            if change and hasattr(obj, 'MEDIA_URL_FIELDS'):
                # Check for file field changes
                for field_name in file_field_names:
                    if field_name in form.changed_data:
                        # File was changed - delete old uploaded file if exists
                        old_obj = obj.__class__.objects.get(pk=obj.pk)
                        old_value = getattr(old_obj, field_name, None)
                        # Only delete if it's an actual uploaded file (has name attribute)
                        if old_value and hasattr(old_value, 'name') and old_value.name:
                            old_id = get_public_id_from_field(old_value)
                            if old_id:
                                logger.info(f"Admin: Deleting old uploaded file {old_id}")
                                delete_file_from_storage(old_value, old_id)
            
            super().save_model(request, obj, form, change)
        
        def delete_model(self, request, obj):
            """Override to cleanup uploaded files on delete."""
            for field_name in file_field_names:
                field_value = getattr(obj, field_name, None)
                # Only delete if it's an actual uploaded file (has name attribute)
                if field_value and hasattr(field_value, 'name') and field_value.name:
                    public_id = get_public_id_from_field(field_value)
                    if public_id:
                        logger.info(f"Admin: Deleting uploaded file {public_id} on model delete")
                        delete_file_from_storage(field_value, public_id)
            
            super().delete_model(request, obj)
        
        def delete_queryset(self, request, queryset):
            """Override to cleanup uploaded files on bulk delete."""
            for obj in queryset:
                for field_name in file_field_names:
                    field_value = getattr(obj, field_name, None)
                    # Only delete if it's an actual uploaded file (has name attribute)
                    if field_value and hasattr(field_value, 'name') and field_value.name:
                        public_id = get_public_id_from_field(field_value)
                        if public_id:
                            logger.info(f"Admin: Deleting uploaded file {public_id} on bulk delete")
                            delete_file_from_storage(field_value, public_id)
            
            super().delete_queryset(request, queryset)
    
    return MediaAdminMixin


# =============================================================================
# SIGNAL-BASED SETUP (Alternative to Mixins)
# =============================================================================

def setup_media_signals(model_class: Type[models.Model], field_mapping: Dict[str, str]):
    """
    Set up signals for a model to handle URL population and file cleanup.
    
    This is an alternative to using mixins - useful for third-party models.
    
    Args:
        model_class: The model class
        field_mapping: Dict mapping file field names to URL field names
    
    Example:
        from utils.media_mixins import setup_media_signals
        from someapp.models import SomeModel
        
        setup_media_signals(SomeModel, {
            'image': 'image_url',
        })
    """
    # Store original files on init
    @receiver(post_init, sender=model_class)
    def store_original_files(sender, instance, **kwargs):
        if not hasattr(instance, '_original_media_files'):
            instance._original_media_files = {}
        
        for file_field in field_mapping.keys():
            try:
                field_value = getattr(instance, file_field, None)
                instance._original_media_files[file_field] = get_public_id_from_field(field_value)
            except Exception:
                instance._original_media_files[file_field] = None
    
    # Handle URL population and cleanup on save
    @receiver(pre_save, sender=model_class)
    def handle_media_changes(sender, instance, **kwargs):
        for file_field, url_field in field_mapping.items():
            original_id = getattr(instance, '_original_media_files', {}).get(file_field)
            current_value = getattr(instance, file_field, None)
            current_id = get_public_id_from_field(current_value)
            
            # Update URL field
            extracted_url = extract_url_from_file_field(current_value)
            if extracted_url:
                setattr(instance, url_field, extracted_url)
            elif original_id and original_id != current_id:
                # File was cleared
                current_url = getattr(instance, url_field, None)
                if current_url and original_id in str(current_url):
                    setattr(instance, url_field, None)
            
            # Delete old file if changed
            if original_id and original_id != current_id:
                delete_file_from_storage(None, original_id)
    
    # Update stored files after save
    @receiver(post_save, sender=model_class)
    def update_stored_files(sender, instance, **kwargs):
        store_original_files(sender, instance)
    
    # Cleanup files on delete
    @receiver(post_delete, sender=model_class)
    def cleanup_on_delete(sender, instance, **kwargs):
        for file_field in field_mapping.keys():
            field_value = getattr(instance, file_field, None)
            if field_value:
                public_id = get_public_id_from_field(field_value)
                if public_id:
                    delete_file_from_storage(field_value, public_id)


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

def populate_url_fields(instance: models.Model, field_mapping: Dict[str, str], force: bool = False) -> bool:
    """
    Standalone function to populate URL fields from file fields.
    
    Args:
        instance: Model instance
        field_mapping: Dict mapping file field names to URL field names
        force: If True, overwrite existing URL values
    
    Returns:
        True if any fields were updated
    """
    updated = False
    
    for file_field_name, url_field_name in field_mapping.items():
        file_value = getattr(instance, file_field_name, None)
        current_url = getattr(instance, url_field_name, None)
        
        extracted_url = extract_url_from_file_field(file_value)
        
        if extracted_url and (not current_url or force):
            setattr(instance, url_field_name, extracted_url)
            updated = True
    
    return updated


def cleanup_orphaned_files(model_class: Type[models.Model], field_mapping: Dict[str, str], dry_run: bool = True) -> List[str]:
    """
    Find and optionally delete files that no longer have associated model instances.
    
    Args:
        model_class: The model class to check
        field_mapping: Dict mapping file field names to URL field names
        dry_run: If True, only report what would be deleted
    
    Returns:
        List of public_ids that were deleted (or would be deleted in dry_run)
    """
    # This is a placeholder - actual implementation would depend on storage backend
    logger.warning("cleanup_orphaned_files is not fully implemented yet")
    return []
