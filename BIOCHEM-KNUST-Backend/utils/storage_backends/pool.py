"""
Media Storage Pool

Load balancing and traffic distribution across multiple storage backends.
This module provides intelligent file distribution across your enabled storage providers.
"""

import random
import logging
from typing import Optional, Union, Dict, Any, List, BinaryIO
from collections import defaultdict
from datetime import datetime

from django.conf import settings
from django.core.files.uploadedfile import UploadedFile

from .base import StorageBackend

logger = logging.getLogger(__name__)


def _get_available_backends():
    """Lazy import to avoid circular dependency."""
    from .cloudinary_backend import CloudinaryBackend
    from .local_backend import LocalStorageBackend
    from .google_drive_backend import GoogleDriveBackend
    from .s3_backend import S3Backend
    from .dropbox_backend import DropboxBackend
    from .azure_blob_backend import AzureBlobBackend
    from .backblaze_b2_backend import BackblazeB2Backend
    
    return {
        'cloudinary': CloudinaryBackend,
        'local': LocalStorageBackend,
        'google_drive': GoogleDriveBackend,
        's3': S3Backend,
        'dropbox': DropboxBackend,
        'azure_blob': AzureBlobBackend,
        'backblaze_b2': BackblazeB2Backend,
    }


class MediaStoragePool:
    """
    A pool of storage backends with load balancing and traffic distribution.
    
    Features:
    - Multiple distribution modes: round_robin, weighted, least_used, random
    - Automatic failover to fallback backends
    - Per-provider upload tracking
    - Enable/disable providers at runtime
    - Health checking
    
    Configuration in settings.py:
    
        MEDIA_STORAGE_POOL = {
            'enabled': True,
            'providers': {
                'cloudinary': {
                    'enabled': True,
                    'weight': 5,  # Higher weight = more traffic
                },
                's3': {
                    'enabled': True,
                    'weight': 3,
                },
                'google_drive': {
                    'enabled': True,
                    'weight': 2,
                },
                'local': {
                    'enabled': True,
                    'weight': 1,  # Fallback/low priority
                },
            },
            'distribution_mode': 'weighted',  # round_robin, weighted, least_used, random
            'fallback_order': ['cloudinary', 's3', 'local'],  # Order for failover
        }
    
    Usage:
        from utils.storage_backends.pool import MediaStoragePool
        
        pool = MediaStoragePool()
        result = pool.upload(file, folder='uploads')
    """
    
    def __init__(self, config: Optional[Dict] = None):
        """Initialize the storage pool with configuration."""
        self.config = config or getattr(settings, 'MEDIA_STORAGE_POOL', {})
        self._backends = {}
        self._usage_counts = defaultdict(int)
        self._round_robin_index = 0
        self._initialize_backends()
    
    def _initialize_backends(self):
        """Initialize enabled backends from configuration."""
        providers_config = self.config.get('providers', {})
        available_backends = _get_available_backends()
        
        for name, provider_config in providers_config.items():
            if not provider_config.get('enabled', False):
                continue
            
            backend_class = available_backends.get(name)
            if backend_class:
                backend = backend_class()
                if backend.is_available():
                    self._backends[name] = {
                        'backend': backend,
                        'weight': provider_config.get('weight', 1),
                        'enabled': True,
                    }
                    logger.info(f"Initialized storage backend: {name}")
                else:
                    logger.warning(f"Backend {name} is configured but not available (check credentials)")
            else:
                logger.warning(f"Unknown backend: {name}")
        
        if not self._backends:
            logger.warning("No storage backends available in pool. Adding local as fallback.")
            local_class = available_backends.get('local')
            if local_class:
                local_backend = local_class()
                if local_backend.is_available():
                    self._backends['local'] = {
                        'backend': local_backend,
                        'weight': 1,
                        'enabled': True,
                    }
    
    def _select_backend(self) -> Optional[tuple]:
        """Select a backend based on distribution mode."""
        enabled = [(name, info) for name, info in self._backends.items() if info['enabled']]
        
        if not enabled:
            return None
        
        mode = self.config.get('distribution_mode', 'round_robin')
        
        if mode == 'round_robin':
            self._round_robin_index = (self._round_robin_index + 1) % len(enabled)
            name, info = enabled[self._round_robin_index]
            return name, info['backend']
        
        elif mode == 'weighted':
            total_weight = sum(info['weight'] for _, info in enabled)
            r = random.uniform(0, total_weight)
            cumulative = 0
            for name, info in enabled:
                cumulative += info['weight']
                if r <= cumulative:
                    return name, info['backend']
            name, info = enabled[-1]
            return name, info['backend']
        
        elif mode == 'least_used':
            min_count = float('inf')
            selected = None
            for name, info in enabled:
                count = self._usage_counts[name]
                if count < min_count:
                    min_count = count
                    selected = (name, info['backend'])
            return selected
        
        elif mode == 'random':
            name, info = random.choice(enabled)
            return name, info['backend']
        
        name, info = enabled[0]
        return name, info['backend']
    
    def upload(
        self,
        file: Union[BinaryIO, UploadedFile, bytes],
        folder: str = "",
        filename: Optional[str] = None,
        resource_type: str = "image",
        preferred_backend: Optional[str] = None,
        **options
    ) -> Dict[str, Any]:
        """
        Upload file to the pool, selecting backend based on distribution mode.
        
        Args:
            file: The file to upload
            folder: Destination folder
            filename: Optional filename override
            resource_type: 'image', 'video', or 'raw'
            preferred_backend: Optional specific backend to use
            **options: Additional backend-specific options
            
        Returns:
            Upload result dict with 'success', 'url', 'provider', etc.
        """
        # Use preferred backend if specified and available
        if preferred_backend and preferred_backend in self._backends:
            backend_info = self._backends[preferred_backend]
            if backend_info['enabled']:
                backend = backend_info['backend']
                result = backend.upload(file, folder, filename, resource_type, **options)
                if result.get('success'):
                    self._usage_counts[preferred_backend] += 1
                    return result
        
        # Select backend based on distribution mode
        selection = self._select_backend()
        if not selection:
            return {
                'success': False,
                'error': 'No available storage backends',
                'url': None,
                'provider': None,
            }
        
        name, backend = selection
        result = backend.upload(file, folder, filename, resource_type, **options)
        
        # If failed, try fallback
        if not result.get('success'):
            fallback_order = self.config.get('fallback_order', [])
            for fallback_name in fallback_order:
                if fallback_name == name:
                    continue
                if fallback_name in self._backends and self._backends[fallback_name]['enabled']:
                    fallback_backend = self._backends[fallback_name]['backend']
                    result = fallback_backend.upload(file, folder, filename, resource_type, **options)
                    if result.get('success'):
                        self._usage_counts[fallback_name] += 1
                        return result
        else:
            self._usage_counts[name] += 1
        
        return result
    
    def enable_backend(self, name: str) -> bool:
        """Enable a backend in the pool."""
        if name in self._backends:
            self._backends[name]['enabled'] = True
            return True
        return False
    
    def disable_backend(self, name: str) -> bool:
        """Disable a backend in the pool."""
        if name in self._backends:
            self._backends[name]['enabled'] = False
            return True
        return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics for all backends."""
        return {
            'backends': {
                name: {
                    'enabled': info['enabled'],
                    'weight': info['weight'],
                    'uploads': self._usage_counts[name],
                    'available': info['backend'].is_available(),
                }
                for name, info in self._backends.items()
            },
            'total_uploads': sum(self._usage_counts.values()),
            'distribution_mode': self.config.get('distribution_mode', 'round_robin'),
        }
    
    def get_available_backends(self) -> List[str]:
        """Get list of available backend names."""
        return [name for name, info in self._backends.items() if info['enabled'] and info['backend'].is_available()]
    
    def health_check(self) -> Dict[str, bool]:
        """Check health of all configured backends."""
        return {
            name: info['backend'].is_available()
            for name, info in self._backends.items()
        }
