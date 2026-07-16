"""
Google Drive Storage Backend

Store files in Google Drive with automatic folder creation and public sharing.
Good for organizations already using Google Workspace.

Website: https://drive.google.com
API Docs: https://developers.google.com/drive/api
"""

import os
import re
import hashlib
import logging
from typing import Optional, Union, Dict, Any, BinaryIO
from datetime import datetime

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from .base import StorageBackend

logger = logging.getLogger(__name__)


class GoogleDriveBackend(StorageBackend):
    """
    Google Drive storage backend.
    Requires google-api-python-client and google-auth packages.
    
    Setup:
    1. Create a Google Cloud Project at https://console.cloud.google.com
    2. Enable the Google Drive API
    3. Create a Service Account and download the JSON credentials
    4. Share your Google Drive folder with the service account email
    5. Configure in settings.py:
    
        GOOGLE_DRIVE_CREDENTIALS = '/path/to/service-account.json'
        # OR as a dict:
        GOOGLE_DRIVE_CREDENTIALS = {
            "type": "service_account",
            "project_id": "your-project-id",
            "private_key_id": "...",
            "private_key": "-----BEGIN PRIVATE KEY-----\\n...\\n-----END PRIVATE KEY-----\\n",
            "client_email": "your-service@your-project.iam.gserviceaccount.com",
            "client_id": "...",
            ...
        }
        GOOGLE_DRIVE_FOLDER_ID = 'your-shared-folder-id'  # Optional
    
    Install:
        pip install google-api-python-client google-auth google-auth-httplib2
    
    Features:
    - Automatic folder creation
    - Public file sharing
    - Supports all file types
    - Thumbnail generation for images
    """
    
    name = "google_drive"
    
    def __init__(self):
        self._service = None
        self._credentials_path = getattr(settings, 'GOOGLE_DRIVE_CREDENTIALS', None)
        self._default_folder_id = getattr(settings, 'GOOGLE_DRIVE_FOLDER_ID', None)
        self._folder_cache = {}
    
    def is_available(self) -> bool:
        """Check if Google Drive is configured."""
        return bool(self._credentials_path)
    
    def _get_service(self):
        """Get or create Google Drive service instance."""
        if self._service is not None:
            return self._service
        
        if not self.is_available():
            return None
        
        try:
            from google.oauth2 import service_account
            from googleapiclient.discovery import build
            
            SCOPES = ['https://www.googleapis.com/auth/drive.file']
            
            if isinstance(self._credentials_path, dict):
                credentials = service_account.Credentials.from_service_account_info(
                    self._credentials_path, scopes=SCOPES
                )
            else:
                credentials = service_account.Credentials.from_service_account_file(
                    self._credentials_path, scopes=SCOPES
                )
            
            self._service = build('drive', 'v3', credentials=credentials)
            return self._service
            
        except ImportError:
            logger.error("Google Drive packages not installed. Run: pip install google-api-python-client google-auth")
            return None
        except Exception as e:
            logger.error(f"Failed to initialize Google Drive service: {e}")
            return None
    
    def _get_or_create_folder(self, folder_path: str, parent_id: Optional[str] = None) -> Optional[str]:
        """Get or create a folder hierarchy in Google Drive."""
        if not folder_path:
            return parent_id or self._default_folder_id
        
        cache_key = f"{parent_id or 'root'}:{folder_path}"
        if cache_key in self._folder_cache:
            return self._folder_cache[cache_key]
        
        service = self._get_service()
        if not service:
            return None
        
        parts = folder_path.strip('/').split('/')
        current_parent = parent_id or self._default_folder_id or 'root'
        
        for part in parts:
            if not part:
                continue
            
            query = f"name='{part}' and mimeType='application/vnd.google-apps.folder' and trashed=false"
            if current_parent != 'root':
                query += f" and '{current_parent}' in parents"
            
            try:
                results = service.files().list(
                    q=query,
                    spaces='drive',
                    fields='files(id, name)'
                ).execute()
                
                files = results.get('files', [])
                
                if files:
                    current_parent = files[0]['id']
                else:
                    file_metadata = {
                        'name': part,
                        'mimeType': 'application/vnd.google-apps.folder'
                    }
                    if current_parent != 'root':
                        file_metadata['parents'] = [current_parent]
                    
                    folder = service.files().create(
                        body=file_metadata,
                        fields='id'
                    ).execute()
                    current_parent = folder.get('id')
                    
            except Exception as e:
                logger.error(f"Failed to get/create Google Drive folder '{part}': {e}")
                return None
        
        self._folder_cache[cache_key] = current_parent
        return current_parent
    
    def _get_mime_type(self, filename: str, resource_type: str) -> str:
        """Determine MIME type from filename or resource type."""
        import mimetypes
        
        mime_type, _ = mimetypes.guess_type(filename)
        if mime_type:
            return mime_type
        
        mime_map = {
            'image': 'image/jpeg',
            'video': 'video/mp4',
            'raw': 'application/octet-stream',
        }
        return mime_map.get(resource_type, 'application/octet-stream')
    
    def upload(
        self,
        file: Union[BinaryIO, UploadedFile, bytes],
        folder: str = "",
        filename: Optional[str] = None,
        resource_type: str = "image",
        **options
    ) -> Dict[str, Any]:
        """Upload file to Google Drive."""
        if not self.is_available():
            return {
                'success': False,
                'error': 'Google Drive is not configured. Set GOOGLE_DRIVE_CREDENTIALS in settings.',
                'url': None,
                'provider': self.name,
            }
        
        service = self._get_service()
        if not service:
            return {
                'success': False,
                'error': 'Failed to initialize Google Drive service',
                'url': None,
                'provider': self.name,
            }
        
        try:
            from googleapiclient.http import MediaIoBaseUpload
            import io
            
            if filename is None:
                if hasattr(file, 'name'):
                    filename = os.path.basename(file.name)
                else:
                    ext = '.jpg' if resource_type == 'image' else '.mp4' if resource_type == 'video' else '.bin'
                    filename = f"{hashlib.md5(str(datetime.now()).encode()).hexdigest()[:12]}{ext}"
            
            parent_id = options.get('parent_id') or self._get_or_create_folder(folder)
            
            if isinstance(file, bytes):
                file_content = io.BytesIO(file)
                file_size = len(file)
            elif hasattr(file, 'read'):
                content = file.read()
                file_content = io.BytesIO(content)
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
            
            mime_type = self._get_mime_type(filename, resource_type)
            
            file_metadata = {'name': filename}
            if parent_id:
                file_metadata['parents'] = [parent_id]
            
            media = MediaIoBaseUpload(
                file_content,
                mimetype=mime_type,
                resumable=True
            )
            
            uploaded_file = service.files().create(
                body=file_metadata,
                media_body=media,
                fields='id, name, webViewLink, webContentLink, size, mimeType'
            ).execute()
            
            file_id = uploaded_file.get('id')
            
            make_public = options.get('make_public', True)
            if make_public:
                try:
                    service.permissions().create(
                        fileId=file_id,
                        body={'type': 'anyone', 'role': 'reader'}
                    ).execute()
                except Exception as e:
                    logger.warning(f"Failed to make file public: {e}")
            
            if resource_type == 'image':
                url = f"https://drive.google.com/uc?export=view&id={file_id}"
            else:
                url = f"https://drive.google.com/uc?export=download&id={file_id}"
            
            return {
                'success': True,
                'url': url,
                'public_id': file_id,
                'resource_type': resource_type,
                'format': os.path.splitext(filename)[1].lstrip('.'),
                'size': file_size,
                'provider': self.name,
                'web_view_link': uploaded_file.get('webViewLink'),
                'web_content_link': uploaded_file.get('webContentLink'),
                'mime_type': mime_type,
            }
            
        except ImportError:
            return {
                'success': False,
                'error': 'Google Drive packages not installed. Run: pip install google-api-python-client google-auth',
                'url': None,
                'provider': self.name,
            }
        except Exception as e:
            logger.error(f"Google Drive upload failed: {e}")
            return {
                'success': False,
                'error': str(e),
                'url': None,
                'provider': self.name,
            }
    
    def delete(self, public_id: str, resource_type: str = "image") -> bool:
        """Delete file from Google Drive."""
        service = self._get_service()
        if not service:
            return False
        
        try:
            service.files().delete(fileId=public_id).execute()
            return True
        except Exception as e:
            logger.error(f"Failed to delete Google Drive file {public_id}: {e}")
            return False
    
    def get_url(
        self,
        identifier: str,
        resource_type: str = "image",
        **transformations
    ) -> Optional[str]:
        """Get URL for Google Drive file."""
        if 'drive.google.com' in identifier:
            patterns = [
                r'/d/([a-zA-Z0-9_-]+)',
                r'id=([a-zA-Z0-9_-]+)',
            ]
            for pattern in patterns:
                match = re.search(pattern, identifier)
                if match:
                    identifier = match.group(1)
                    break
        
        size = transformations.get('size', '')
        
        if resource_type == 'image':
            if size == 'thumbnail':
                return f"https://drive.google.com/thumbnail?id={identifier}&sz=w200"
            elif size == 'small':
                return f"https://drive.google.com/thumbnail?id={identifier}&sz=w400"
            elif size == 'medium':
                return f"https://drive.google.com/thumbnail?id={identifier}&sz=w800"
            elif size == 'large':
                return f"https://drive.google.com/thumbnail?id={identifier}&sz=w1200"
            else:
                return f"https://drive.google.com/uc?export=view&id={identifier}"
        else:
            return f"https://drive.google.com/uc?export=download&id={identifier}"
    
    def optimize_url(
        self,
        url: str,
        width: Optional[int] = None,
        height: Optional[int] = None,
        quality: str = "auto",
        format: str = "auto"
    ) -> str:
        """Optimize Google Drive URL for different sizes."""
        if 'drive.google.com' not in url:
            return url
        
        patterns = [
            r'/d/([a-zA-Z0-9_-]+)',
            r'id=([a-zA-Z0-9_-]+)',
        ]
        file_id = None
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                file_id = match.group(1)
                break
        
        if not file_id:
            return url
        
        if width:
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=w{width}"
        elif height:
            return f"https://drive.google.com/thumbnail?id={file_id}&sz=h{height}"
        
        return url
