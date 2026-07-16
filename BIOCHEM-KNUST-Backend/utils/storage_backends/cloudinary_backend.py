"""
Cloudinary Storage Backend

Cloud-based image and video hosting with automatic optimization.
Website: https://cloudinary.com

This is the recommended primary storage for production environments
due to its robust CDN, automatic optimization, and transformation capabilities.
"""

import os
import re
import logging
from typing import Optional, Union, Dict, Any, BinaryIO

from django.core.files.uploadedfile import UploadedFile

from .base import StorageBackend

logger = logging.getLogger(__name__)


class CloudinaryBackend(StorageBackend):
    """
    Cloudinary storage backend.
    Uses the existing Cloudinary configuration from Django settings.
    
    Setup:
    1. Create a Cloudinary account at https://cloudinary.com
    2. Install: pip install cloudinary
    3. Configure in settings.py:
    
        import cloudinary
        cloudinary.config(
            cloud_name='your-cloud-name',
            api_key='your-api-key',
            api_secret='your-api-secret',
            secure=True
        )
    
    Features:
    - Automatic image optimization
    - On-the-fly transformations (resize, crop, format conversion)
    - Global CDN delivery
    - Video support with streaming
    """
    
    name = "cloudinary"
    
    def __init__(self):
        self._configured = None
    
    def is_available(self) -> bool:
        """Check if Cloudinary is configured."""
        if self._configured is not None:
            return self._configured
        
        try:
            import cloudinary
            config = cloudinary.config()
            self._configured = bool(config.cloud_name and config.api_key and config.api_secret)
            return self._configured
        except ImportError:
            self._configured = False
            return False
        except Exception as e:
            logger.error(f"Cloudinary configuration check failed: {e}")
            self._configured = False
            return False
    
    def upload(
        self,
        file: Union[BinaryIO, UploadedFile, bytes],
        folder: str = "",
        filename: Optional[str] = None,
        resource_type: str = "image",
        **options
    ) -> Dict[str, Any]:
        """Upload file to Cloudinary."""
        if not self.is_available():
            return {
                'success': False,
                'error': 'Cloudinary is not configured',
                'url': None,
                'provider': self.name,
            }
        
        try:
            import cloudinary.uploader
            
            upload_options = {
                'folder': folder,
                'resource_type': resource_type,
                'use_filename': True,
                'unique_filename': True,
                'overwrite': False,
            }
            
            if filename:
                upload_options['public_id'] = os.path.splitext(filename)[0]
            
            upload_options.update(options)
            
            if isinstance(file, bytes):
                result = cloudinary.uploader.upload(file, **upload_options)
            elif hasattr(file, 'read'):
                result = cloudinary.uploader.upload(file, **upload_options)
            else:
                result = cloudinary.uploader.upload(file, **upload_options)
            
            return {
                'success': True,
                'url': result.get('secure_url') or result.get('url'),
                'public_id': result.get('public_id'),
                'resource_type': result.get('resource_type'),
                'format': result.get('format'),
                'size': result.get('bytes', 0),
                'width': result.get('width'),
                'height': result.get('height'),
                'original_filename': result.get('original_filename'),
                'provider': self.name,
            }
            
        except Exception as e:
            logger.error(f"Cloudinary upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': None,
                'provider': self.name,
            }
    
    def delete(self, public_id: str, resource_type: str = "image") -> bool:
        """Delete file from Cloudinary."""
        if not self.is_available():
            return False
        
        try:
            import cloudinary.uploader
            result = cloudinary.uploader.destroy(public_id, resource_type=resource_type)
            return result.get('result') == 'ok'
        except Exception as e:
            logger.error(f"Cloudinary delete failed: {e}")
            return False
    
    def get_url(
        self,
        identifier: str,
        resource_type: str = "image",
        **transformations
    ) -> Optional[str]:
        """Get URL for Cloudinary resource."""
        if not self.is_available():
            return None
        
        try:
            import cloudinary
            from cloudinary import CloudinaryResource
            
            resource = CloudinaryResource(identifier, resource_type=resource_type)
            return resource.build_url(**transformations, secure=True)
        except Exception as e:
            logger.error(f"Cloudinary URL generation failed: {e}")
            return None
    
    def optimize_url(
        self,
        url: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        quality: str = "auto",
        format: str = "auto",
        crop: Optional[str] = None
    ) -> str:
        """Optimize Cloudinary URL with transformations."""
        if not url:
            return url
        
        if url.startswith('http://'):
            url = url.replace('http://', 'https://', 1)
        
        if 'cloudinary.com' not in url:
            return url
        
        transformations = [f"f_{format}", f"q_{quality}"]
        
        if width:
            transformations.append(f"w_{width}")
        if height:
            transformations.append(f"h_{height}")
        if crop:
            transformations.append(f"c_{crop}")
        
        transform_str = ",".join(transformations)
        
        if '/upload/f_' in url or '/upload/q_' in url or '/upload/w_' in url:
            return url
        
        pattern = r'(/upload/)([^/])'
        replacement = rf'\1{transform_str}/\2'
        
        return re.sub(pattern, replacement, url)
