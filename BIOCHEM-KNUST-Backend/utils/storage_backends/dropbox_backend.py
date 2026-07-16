"""
Dropbox Storage Backend

Store files in Dropbox with automatic sharing link generation.
Good for teams already using Dropbox for file storage.

Website: https://www.dropbox.com
API Docs: https://www.dropbox.com/developers
"""

import os
import hashlib
import logging
from typing import Optional, Union, Dict, Any, BinaryIO
from datetime import datetime

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from .base import StorageBackend

logger = logging.getLogger(__name__)


class DropboxBackend(StorageBackend):
    """
    Dropbox storage backend.
    
    Setup:
    1. Create a Dropbox App at https://www.dropbox.com/developers/apps
    2. Generate an access token (or use OAuth2)
    3. Configure in settings.py:
    
        DROPBOX_ACCESS_TOKEN = 'your-access-token'
        DROPBOX_APP_KEY = 'your-app-key'  # Optional
        DROPBOX_APP_SECRET = 'your-app-secret'  # Optional
        DROPBOX_ROOT_FOLDER = '/css-uploads'  # Optional: default folder
    
    Install:
        pip install dropbox
    
    Features:
    - 2GB free storage
    - Automatic shared link generation
    - File versioning
    - Team folder support
    """
    
    name = "dropbox"
    
    def __init__(self):
        self._client = None
        self.access_token = getattr(settings, 'DROPBOX_ACCESS_TOKEN', None)
        self.app_key = getattr(settings, 'DROPBOX_APP_KEY', None)
        self.app_secret = getattr(settings, 'DROPBOX_APP_SECRET', None)
        self.root_folder = getattr(settings, 'DROPBOX_ROOT_FOLDER', '/css-uploads')
    
    def is_available(self) -> bool:
        """Check if Dropbox is configured."""
        return bool(self.access_token)
    
    def _get_client(self):
        """Get or create Dropbox client."""
        if self._client is not None:
            return self._client
        
        if not self.is_available():
            return None
        
        try:
            import dropbox
            
            self._client = dropbox.Dropbox(self.access_token)
            return self._client
            
        except ImportError:
            logger.error("dropbox not installed. Run: pip install dropbox")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Dropbox client: {e}")
            return None
    
    def upload(
        self,
        file: Union[BinaryIO, UploadedFile, bytes],
        folder: str = "",
        filename: Optional[str] = None,
        resource_type: str = "image",
        **options
    ) -> Dict[str, Any]:
        """Upload file to Dropbox."""
        if not self.is_available():
            return {
                'success': False,
                'error': 'Dropbox is not configured. Set DROPBOX_ACCESS_TOKEN in settings.',
                'url': None,
                'provider': self.name,
            }
        
        client = self._get_client()
        if not client:
            return {
                'success': False,
                'error': 'Failed to initialize Dropbox client',
                'url': None,
                'provider': self.name,
            }
        
        try:
            import dropbox
            
            if filename is None:
                if hasattr(file, 'name'):
                    filename = os.path.basename(file.name)
                else:
                    ext = '.jpg' if resource_type == 'image' else '.mp4' if resource_type == 'video' else '.bin'
                    filename = f"{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]}{ext}"
            
            date_path = datetime.now().strftime('%Y/%m')
            if folder:
                dropbox_path = f"{self.root_folder}/{folder}/{date_path}/{filename}"
            else:
                dropbox_path = f"{self.root_folder}/{date_path}/{filename}"
            
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
            
            result = client.files_upload(
                file_content,
                dropbox_path,
                mode=dropbox.files.WriteMode.overwrite
            )
            
            try:
                shared_link = client.sharing_create_shared_link_with_settings(dropbox_path)
                url = shared_link.url.replace('?dl=0', '?raw=1')
            except dropbox.exceptions.ApiError as e:
                if e.error.is_shared_link_already_exists():
                    links = client.sharing_list_shared_links(path=dropbox_path)
                    if links.links:
                        url = links.links[0].url.replace('?dl=0', '?raw=1')
                    else:
                        url = None
                else:
                    url = None
            
            return {
                'success': True,
                'url': url,
                'public_id': dropbox_path,
                'resource_type': resource_type,
                'format': os.path.splitext(filename)[1].lstrip('.'),
                'size': file_size,
                'provider': self.name,
                'dropbox_path': dropbox_path,
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'dropbox package not installed. Run: pip install dropbox',
                'url': None,
                'provider': self.name,
            }
        except Exception as e:
            logger.error(f"Dropbox upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': None,
                'provider': self.name,
            }
    
    def delete(self, public_id: str, resource_type: str = "image") -> bool:
        """Delete file from Dropbox."""
        client = self._get_client()
        if not client:
            return False
        
        try:
            client.files_delete_v2(public_id)
            return True
        except Exception as e:
            logger.error(f"Failed to delete Dropbox file {public_id}: {e}")
            return False
    
    def get_url(
        self,
        identifier: str,
        resource_type: str = "image",
        **transformations
    ) -> Optional[str]:
        """Get URL for Dropbox file."""
        client = self._get_client()
        if not client:
            return None
        
        try:
            links = client.sharing_list_shared_links(path=identifier)
            if links.links:
                return links.links[0].url.replace('?dl=0', '?raw=1')
            return None
        except Exception:
            return None
