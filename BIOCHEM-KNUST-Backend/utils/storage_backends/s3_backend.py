"""
Amazon S3 Storage Backend

Amazon S3 or S3-compatible storage (DigitalOcean Spaces, MinIO, Wasabi, etc.)
Industry standard for scalable cloud storage.

Website: https://aws.amazon.com/s3/
"""

import os
import io
import hashlib
import logging
import mimetypes
from typing import Optional, Union, Dict, Any, BinaryIO
from datetime import datetime

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from .base import StorageBackend

logger = logging.getLogger(__name__)


class S3Backend(StorageBackend):
    """
    Amazon S3 or S3-compatible storage backend.
    Works with AWS S3, DigitalOcean Spaces, MinIO, Wasabi, etc.
    
    Setup:
    1. Create an S3 bucket (or compatible service)
    2. Configure in settings.py:
    
        AWS_ACCESS_KEY_ID = 'your-access-key'
        AWS_SECRET_ACCESS_KEY = 'your-secret-key'
        AWS_STORAGE_BUCKET_NAME = 'your-bucket-name'
        AWS_S3_REGION_NAME = 'us-east-1'  # Optional
        AWS_S3_ENDPOINT_URL = 'https://...'  # For S3-compatible services
        AWS_S3_CUSTOM_DOMAIN = 'cdn.example.com'  # Optional CDN domain
    
    Install:
        pip install boto3
    
    Features:
    - Highly scalable
    - S3-compatible (works with many providers)
    - CDN integration support
    - Fine-grained access control
    """
    
    name = "s3"
    
    def __init__(self):
        self._client = None
        self.access_key = getattr(settings, 'AWS_ACCESS_KEY_ID', None)
        self.secret_key = getattr(settings, 'AWS_SECRET_ACCESS_KEY', None)
        self.bucket_name = getattr(settings, 'AWS_STORAGE_BUCKET_NAME', None)
        self.region = getattr(settings, 'AWS_S3_REGION_NAME', 'us-east-1')
        self.endpoint_url = getattr(settings, 'AWS_S3_ENDPOINT_URL', None)
        self.custom_domain = getattr(settings, 'AWS_S3_CUSTOM_DOMAIN', None)
    
    def is_available(self) -> bool:
        """Check if S3 is configured."""
        return all([self.access_key, self.secret_key, self.bucket_name])
    
    def _get_client(self):
        """Get or create S3 client."""
        if self._client is not None:
            return self._client
        
        if not self.is_available():
            return None
        
        try:
            import boto3
            
            client_kwargs = {
                'aws_access_key_id': self.access_key,
                'aws_secret_access_key': self.secret_key,
                'region_name': self.region,
            }
            if self.endpoint_url:
                client_kwargs['endpoint_url'] = self.endpoint_url
            
            self._client = boto3.client('s3', **client_kwargs)
            return self._client
            
        except ImportError:
            logger.error("boto3 not installed. Run: pip install boto3")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize S3 client: {e}")
            return None
    
    def upload(
        self,
        file: Union[BinaryIO, UploadedFile, bytes],
        folder: str = "",
        filename: Optional[str] = None,
        resource_type: str = "image",
        **options
    ) -> Dict[str, Any]:
        """Upload file to S3."""
        if not self.is_available():
            return {
                'success': False,
                'error': 'S3 is not configured. Set AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY, and AWS_STORAGE_BUCKET_NAME.',
                'url': None,
                'provider': self.name,
            }
        
        client = self._get_client()
        if not client:
            return {
                'success': False,
                'error': 'Failed to initialize S3 client',
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
                s3_key = f"{folder}/{date_path}/{filename}"
            else:
                s3_key = f"{date_path}/{filename}"
            
            if isinstance(file, bytes):
                file_obj = io.BytesIO(file)
                file_size = len(file)
            elif hasattr(file, 'read'):
                content = file.read()
                file_obj = io.BytesIO(content)
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
            
            content_type, _ = mimetypes.guess_type(filename)
            if not content_type:
                content_type = 'application/octet-stream'
            
            extra_args = {
                'ContentType': content_type,
                'ACL': options.get('acl', 'public-read'),
            }
            
            client.upload_fileobj(file_obj, self.bucket_name, s3_key, ExtraArgs=extra_args)
            
            if self.custom_domain:
                url = f"https://{self.custom_domain}/{s3_key}"
            elif self.endpoint_url:
                url = f"{self.endpoint_url}/{self.bucket_name}/{s3_key}"
            else:
                url = f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{s3_key}"
            
            return {
                'success': True,
                'url': url,
                'public_id': s3_key,
                'resource_type': resource_type,
                'format': os.path.splitext(filename)[1].lstrip('.'),
                'size': file_size,
                'provider': self.name,
                'bucket': self.bucket_name,
            }
            
        except Exception as e:
            logger.error(f"S3 upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': None,
                'provider': self.name,
            }
    
    def delete(self, public_id: str, resource_type: str = "image") -> bool:
        """Delete file from S3."""
        client = self._get_client()
        if not client:
            return False
        
        try:
            client.delete_object(Bucket=self.bucket_name, Key=public_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete S3 file {public_id}: {e}")
            return False
    
    def get_url(
        self,
        identifier: str,
        resource_type: str = "image",
        **transformations
    ) -> Optional[str]:
        """Get URL for S3 file."""
        if self.custom_domain:
            return f"https://{self.custom_domain}/{identifier}"
        elif self.endpoint_url:
            return f"{self.endpoint_url}/{self.bucket_name}/{identifier}"
        else:
            return f"https://{self.bucket_name}.s3.{self.region}.amazonaws.com/{identifier}"
