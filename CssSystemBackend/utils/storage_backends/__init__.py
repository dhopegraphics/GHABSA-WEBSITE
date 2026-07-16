"""
Storage Backends Package

This package contains modular storage backend implementations for the media storage system.
Each backend is in its own file for easy maintenance and can be enabled/disabled independently.

Available backends:
- CloudinaryBackend: Cloud-based image/video hosting (cloudinary.com)
- LocalStorageBackend: Local file system storage
- GoogleDriveBackend: Google Drive cloud storage
- S3Backend: Amazon S3 or S3-compatible services
- DropboxBackend: Dropbox cloud storage
- AzureBlobBackend: Microsoft Azure Blob Storage
- BackblazeB2Backend: Backblaze B2 cloud storage (cost-effective)

Usage:
    from utils.storage_backends import (
        StorageBackend,
        CloudinaryBackend,
        LocalStorageBackend,
        MediaStoragePool,
        # ... other backends as needed
    )

Pool usage:
    from utils.storage_backends import MediaStoragePool
    
    pool = MediaStoragePool()
    result = pool.upload(file, folder='uploads')
"""

from .base import StorageBackend
from .cloudinary_backend import CloudinaryBackend
from .local_backend import LocalStorageBackend
from .google_drive_backend import GoogleDriveBackend
from .s3_backend import S3Backend
from .dropbox_backend import DropboxBackend
from .azure_blob_backend import AzureBlobBackend
from .backblaze_b2_backend import BackblazeB2Backend
from .pool import MediaStoragePool

# Registry of all available backends
AVAILABLE_BACKENDS = {
    'cloudinary': CloudinaryBackend,
    'local': LocalStorageBackend,
    'google_drive': GoogleDriveBackend,
    's3': S3Backend,
    'dropbox': DropboxBackend,
    'azure_blob': AzureBlobBackend,
    'backblaze_b2': BackblazeB2Backend,
}

__all__ = [
    'StorageBackend',
    'CloudinaryBackend',
    'LocalStorageBackend',
    'GoogleDriveBackend',
    'S3Backend',
    'DropboxBackend',
    'AzureBlobBackend',
    'BackblazeB2Backend',
    'MediaStoragePool',
    'AVAILABLE_BACKENDS',
]
