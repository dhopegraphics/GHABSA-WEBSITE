"""
Backblaze B2 Storage Backend

Cost-effective cloud storage, much cheaper than S3 for storage-heavy applications.
Great for archival, backups, and media storage.

Website: https://www.backblaze.com/b2/
"""

import os
import io
import hashlib
import logging
from typing import Optional, Union, Dict, Any, BinaryIO
from datetime import datetime

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from .base import StorageBackend

logger = logging.getLogger(__name__)


class BackblazeB2Backend(StorageBackend):
    """
    Backblaze B2 Cloud Storage backend.
    Much cheaper than S3 for storage-heavy applications.
    
    Setup:
    1. Create a Backblaze B2 account
    2. Create a bucket
    3. Create an application key
    4. Configure in settings.py:
    
        B2_APPLICATION_KEY_ID = 'your-key-id'
        B2_APPLICATION_KEY = 'your-application-key'
        B2_BUCKET_NAME = 'your-bucket-name'
        B2_BUCKET_ID = 'your-bucket-id'  # Optional but faster
    
    Install:
        pip install b2sdk
    
    Features:
    - First 10GB free
    - $0.005/GB/month (vs $0.023 for S3)
    - Free egress to Cloudflare CDN
    - S3-compatible API available
    
    Pricing (as of 2024):
    - Storage: $0.005/GB/month
    - Download: $0.01/GB (first 1GB/day free)
    - Class A transactions: Free
    - Class B transactions: $0.004/10,000
    """
    
    name = "backblaze_b2"
    
    def __init__(self):
        self._api = None
        self._bucket = None
        self.key_id = getattr(settings, 'B2_APPLICATION_KEY_ID', None)
        self.app_key = getattr(settings, 'B2_APPLICATION_KEY', None)
        self.bucket_name = getattr(settings, 'B2_BUCKET_NAME', None)
        self.bucket_id = getattr(settings, 'B2_BUCKET_ID', None)
    
    def is_available(self) -> bool:
        """Check if B2 is configured."""
        return all([self.key_id, self.app_key, self.bucket_name])
    
    def _get_bucket(self):
        """Get or create B2 bucket instance."""
        if self._bucket is not None:
            return self._bucket
        
        if not self.is_available():
            return None
        
        try:
            from b2sdk.v2 import InMemoryAccountInfo, B2Api
            
            info = InMemoryAccountInfo()
            self._api = B2Api(info)
            self._api.authorize_account("production", self.key_id, self.app_key)
            
            if self.bucket_id:
                self._bucket = self._api.get_bucket_by_id(self.bucket_id)
            else:
                self._bucket = self._api.get_bucket_by_name(self.bucket_name)
            
            return self._bucket
            
        except ImportError:
            logger.error("b2sdk not installed. Run: pip install b2sdk")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize B2 bucket: {e}")
            return None
    
    def upload(
        self,
        file: Union[BinaryIO, UploadedFile, bytes],
        folder: str = "",
        filename: Optional[str] = None,
        resource_type: str = "image",
        **options
    ) -> Dict[str, Any]:
        """Upload file to Backblaze B2."""
        if not self.is_available():
            return {
                'success': False,
                'error': 'Backblaze B2 is not configured.',
                'url': None,
                'provider': self.name,
            }
        
        bucket = self._get_bucket()
        if not bucket:
            return {
                'success': False,
                'error': 'Failed to get B2 bucket',
                'url': None,
                'provider': self.name,
            }
        
        try:
            if filename is None:
                if hasattr(file, 'name'):
                    filename = os.path.basename(file.name)
                else:
                    ext = '.jpg' if resource_type == 'image' else '.mp4' if resource_type == 'video' else '.bin'
                    filename = f"{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]}{ext}"
            
            date_path = datetime.now().strftime('%Y/%m')
            if folder:
                b2_file_name = f"{folder}/{date_path}/{filename}"
            else:
                b2_file_name = f"{date_path}/{filename}"
            
            if isinstance(file, bytes):
                file_data = io.BytesIO(file)
                file_size = len(file)
            elif hasattr(file, 'read'):
                content = file.read()
                file_data = io.BytesIO(content)
                file_size = len(content)
                if hasattr(file, 'seek'):
                    file.seek(0)
            else:
                return {
                    'success': False,
                    'error': 'Invalid file type',
                    'url': None,
                    'provider': self.name,
                }
            
            file_info = bucket.upload_bytes(
                file_data.getvalue(),
                b2_file_name
            )
            
            url = self._api.get_download_url_for_fileid(file_info.id_)
            
            return {
                'success': True,
                'url': url,
                'public_id': file_info.id_,
                'resource_type': resource_type,
                'format': os.path.splitext(filename)[1].lstrip('.'),
                'size': file_size,
                'provider': self.name,
                'file_name': b2_file_name,
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'b2sdk not installed. Run: pip install b2sdk',
                'url': None,
                'provider': self.name,
            }
        except Exception as e:
            logger.error(f"B2 upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': None,
                'provider': self.name,
            }
    
    def delete(self, public_id: str, resource_type: str = "image") -> bool:
        """Delete file from B2."""
        if not self._api:
            self._get_bucket()
        
        if not self._api:
            return False
        
        try:
            self._api.delete_file_version(public_id, "")
            return True
        except Exception as e:
            logger.error(f"Failed to delete B2 file {public_id}: {e}")
            return False
    
    def get_url(
        self,
        identifier: str,
        resource_type: str = "image",
        **transformations
    ) -> Optional[str]:
        """Get URL for B2 file."""
        if not self._api:
            self._get_bucket()
        
        if not self._api:
            return None
        
        try:
            return self._api.get_download_url_for_fileid(identifier)
        except Exception:
            return None
