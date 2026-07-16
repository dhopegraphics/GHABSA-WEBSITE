"""
Azure Blob Storage Backend

Microsoft Azure Blob Storage for scalable cloud storage.
Good for organizations using Microsoft Azure ecosystem.

Website: https://azure.microsoft.com/en-us/services/storage/blobs/
"""

import os
import hashlib
import logging
import mimetypes
from typing import Optional, Union, Dict, Any, BinaryIO
from datetime import datetime

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from .base import StorageBackend

logger = logging.getLogger(__name__)


class AzureBlobBackend(StorageBackend):
    """
    Azure Blob Storage backend.
    
    Setup:
    1. Create an Azure Storage Account
    2. Create a container
    3. Configure in settings.py:
    
        AZURE_STORAGE_CONNECTION_STRING = 'your-connection-string'
        # OR use account credentials:
        AZURE_STORAGE_ACCOUNT_NAME = 'your-account-name'
        AZURE_STORAGE_ACCOUNT_KEY = 'your-account-key'
        AZURE_STORAGE_CONTAINER_NAME = 'your-container-name'
        AZURE_STORAGE_CUSTOM_DOMAIN = 'cdn.example.com'  # Optional
    
    Install:
        pip install azure-storage-blob
    
    Features:
    - Integrates with Azure ecosystem
    - Hot, cool, and archive storage tiers
    - CDN integration
    - Strong security features
    """
    
    name = "azure_blob"
    
    def __init__(self):
        self._client = None
        self.connection_string = getattr(settings, 'AZURE_STORAGE_CONNECTION_STRING', None)
        self.account_name = getattr(settings, 'AZURE_STORAGE_ACCOUNT_NAME', None)
        self.account_key = getattr(settings, 'AZURE_STORAGE_ACCOUNT_KEY', None)
        self.container_name = getattr(settings, 'AZURE_STORAGE_CONTAINER_NAME', 'uploads')
        self.custom_domain = getattr(settings, 'AZURE_STORAGE_CUSTOM_DOMAIN', None)
    
    def is_available(self) -> bool:
        """Check if Azure Blob is configured."""
        return bool(self.connection_string or (self.account_name and self.account_key))
    
    def _get_client(self):
        """Get or create Azure Blob service client."""
        if self._client is not None:
            return self._client
        
        if not self.is_available():
            return None
        
        try:
            from azure.storage.blob import BlobServiceClient
            
            if self.connection_string:
                self._client = BlobServiceClient.from_connection_string(self.connection_string)
            else:
                account_url = f"https://{self.account_name}.blob.core.windows.net"
                self._client = BlobServiceClient(
                    account_url=account_url,
                    credential=self.account_key
                )
            return self._client
            
        except ImportError:
            logger.error("azure-storage-blob not installed. Run: pip install azure-storage-blob")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Azure Blob client: {e}")
            return None
    
    def upload(
        self,
        file: Union[BinaryIO, UploadedFile, bytes],
        folder: str = "",
        filename: Optional[str] = None,
        resource_type: str = "image",
        **options
    ) -> Dict[str, Any]:
        """Upload file to Azure Blob Storage."""
        if not self.is_available():
            return {
                'success': False,
                'error': 'Azure Blob Storage is not configured.',
                'url': None,
                'provider': self.name,
            }
        
        service_client = self._get_client()
        if not service_client:
            return {
                'success': False,
                'error': 'Failed to initialize Azure Blob client',
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
                blob_name = f"{folder}/{date_path}/{filename}"
            else:
                blob_name = f"{date_path}/{filename}"
            
            if isinstance(file, bytes):
                file_content = file
                file_size = len(file)
            elif hasattr(file, 'read'):
                file_content = file.read()
                file_size = len(file_content)
                if hasattr(file, 'seek'):
                    file.seek(0)
            else:
                return {
                    'success': False,
                    'error': 'Invalid file type',
                    'url': None,
                    'provider': self.name,
                }
            
            container_client = service_client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(blob_name)
            
            content_type, _ = mimetypes.guess_type(filename)
            
            blob_client.upload_blob(
                file_content,
                overwrite=True,
                content_settings={'content_type': content_type} if content_type else None
            )
            
            if self.custom_domain:
                url = f"https://{self.custom_domain}/{self.container_name}/{blob_name}"
            else:
                url = f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{blob_name}"
            
            return {
                'success': True,
                'url': url,
                'public_id': blob_name,
                'resource_type': resource_type,
                'format': os.path.splitext(filename)[1].lstrip('.'),
                'size': file_size,
                'provider': self.name,
                'container': self.container_name,
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'azure-storage-blob not installed. Run: pip install azure-storage-blob',
                'url': None,
                'provider': self.name,
            }
        except Exception as e:
            logger.error(f"Azure Blob upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': None,
                'provider': self.name,
            }
    
    def delete(self, public_id: str, resource_type: str = "image") -> bool:
        """Delete file from Azure Blob Storage."""
        service_client = self._get_client()
        if not service_client:
            return False
        
        try:
            container_client = service_client.get_container_client(self.container_name)
            blob_client = container_client.get_blob_client(public_id)
            blob_client.delete_blob()
            return True
        except Exception as e:
            logger.error(f"Failed to delete Azure Blob {public_id}: {e}")
            return False
    
    def get_url(
        self,
        identifier: str,
        resource_type: str = "image",
        **transformations
    ) -> Optional[str]:
        """Get URL for Azure Blob file."""
        if self.custom_domain:
            return f"https://{self.custom_domain}/{self.container_name}/{identifier}"
        else:
            return f"https://{self.account_name}.blob.core.windows.net/{self.container_name}/{identifier}"
