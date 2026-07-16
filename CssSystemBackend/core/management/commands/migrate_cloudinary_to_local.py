"""
Django Management Command: Migrate Cloudinary Files to Local Storage

This command:
1. Scans all models with CloudinaryField or image URLs pointing to Cloudinary
2. Downloads each file from Cloudinary
3. Saves to local storage (MEDIA_ROOT)
4. Updates the URL field to point to local storage
5. Optionally clears the CloudinaryField

Usage:
    python manage.py migrate_cloudinary_to_local
    python manage.py migrate_cloudinary_to_local --dry-run  # Preview only
    python manage.py migrate_cloudinary_to_local --model=products.Product  # Specific model
    python manage.py migrate_cloudinary_to_local --delete-from-cloudinary  # Delete after migration
"""

import os
import re
import requests
import hashlib
from datetime import datetime
from urllib.parse import urlparse, unquote
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from django.apps import apps
from django.db import transaction


class Command(BaseCommand):
    help = 'Migrate all Cloudinary files to local storage and update URLs'
    
    # Models and their file field -> URL field mappings
    MODEL_MAPPINGS = {
        'faculty.Staff': {'image': 'image_url'},
        'academics.Lecturer': {'profile_image': 'profile_image_url'},
        'academics.AcademicSlides': {'file': 'file_url'},
        'academics.PastQuestions': {'file': 'file_url'},
        'academics.InternshipOpportunities': {'image': 'image_url'},
        'products.Product': {'product_image': 'product_image_url'},
        'products.ProductColorImage': {'color_image': 'color_image_url'},
        'donations.DonationWithdrawal': {'receipt_image': 'receipt_image_url'},
        'planner.TaskAttachment': {'file': 'file_url'},
        'projects.Project': {'image': 'image_url', 'image2': 'image2_url', 'image3': 'image3_url'},
        'voting.VotingEvent': {'banner_image': 'banner_image_url'},
        'voting.Candidate': {'profile_image': 'profile_image_url'},
        'voting.PollOption': {'image': 'image_url'},
        'codequest.CodeQuestProject': {'app_logo': 'app_logo_url'},
        'codequest.CodeQuestConsultant': {'profile_image': 'profile_image_url'},
        'news.News': {'head_image': 'head_image_url', 'back_image': 'back_image_url'},
        'admissions.AdmissionGuideline': {'image': 'image_url'},
        'history.SocietyHistory': {'image': 'image_url'},
        'history.HistoricalLeader': {'image': 'image_url'},
        'executives.Executive': {'image': 'image_url'},
        'executives.Appointee': {'image': 'image_url'},
        'advertisements.Advertisement': {'flyer': 'flyer_url'},
        'events.Event': {'event_image_1': 'event_image_1_url', 'event_image_2': 'event_image_2_url'},
        'events.SyncMemoAlbum': {'cover_photo': 'cover_photo_url'},
        'events.SyncMemoPhoto': {'photo': 'photo_url'},
        'timeline.Timeline': {'image': 'image_url'},
        'helpdesk.RequestImage': {'image': 'image_url', 'thumbnail': 'thumbnail_url'},
    }
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview what would be migrated without making changes',
        )
        parser.add_argument(
            '--model',
            type=str,
            help='Migrate only a specific model (e.g., products.Product)',
        )
        parser.add_argument(
            '--delete-from-cloudinary',
            action='store_true',
            help='Delete files from Cloudinary after successful migration',
        )
        parser.add_argument(
            '--skip-existing',
            action='store_true',
            default=True,
            help='Skip files that already exist locally (default: True)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=50,
            help='Number of records to process in each batch',
        )
        parser.add_argument(
            '--site-url',
            type=str,
            help='Override SITE_URL for generated URLs (e.g., https://api.biochemknust.com)',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        self.delete_from_cloudinary = options['delete_from_cloudinary']
        self.skip_existing = options['skip_existing']
        self.batch_size = options['batch_size']
        self.specific_model = options['model']
        
        # Setup
        self.media_root = getattr(settings, 'MEDIA_ROOT', '')
        self.media_url = getattr(settings, 'MEDIA_URL', '/media/')
        
        # Allow command-line override of SITE_URL
        if options.get('site_url'):
            self.site_url = options['site_url']
        else:
            self.site_url = getattr(settings, 'SITE_URL', '') or getattr(settings, 'BASE_URL', '')
        
        if not self.media_root:
            raise CommandError('MEDIA_ROOT is not configured in settings')
        
        # Ensure media root exists
        os.makedirs(self.media_root, exist_ok=True)
        
        # Statistics
        self.stats = {
            'total_scanned': 0,
            'total_migrated': 0,
            'total_skipped': 0,
            'total_errors': 0,
            'total_bytes': 0,
        }
        
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('CLOUDINARY TO LOCAL STORAGE MIGRATION'))
        self.stdout.write(self.style.WARNING('=' * 60))
        
        if self.dry_run:
            self.stdout.write(self.style.NOTICE('\n>>> DRY RUN MODE - No changes will be made <<<\n'))
        
        self.stdout.write(f'Media Root: {self.media_root}')
        self.stdout.write(f'Media URL: {self.media_url}')
        self.stdout.write(f'Site URL: {self.site_url or "(not set)"}')
        self.stdout.write('')
        
        # Process models
        models_to_process = self.MODEL_MAPPINGS
        if self.specific_model:
            if self.specific_model in models_to_process:
                models_to_process = {self.specific_model: models_to_process[self.specific_model]}
            else:
                raise CommandError(f'Unknown model: {self.specific_model}')
        
        for model_path, field_mapping in models_to_process.items():
            self.process_model(model_path, field_mapping)
        
        # Print summary
        self.print_summary()
    
    def process_model(self, model_path, field_mapping):
        """Process a single model's Cloudinary files."""
        try:
            app_label, model_name = model_path.split('.')
            Model = apps.get_model(app_label, model_name)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Could not load model {model_path}: {e}'))
            return
        
        self.stdout.write(self.style.HTTP_INFO(f'\n--- Processing {model_path} ---'))
        
        # Get all records
        queryset = Model.objects.all()
        total = queryset.count()
        
        if total == 0:
            self.stdout.write(f'  No records found')
            return
        
        self.stdout.write(f'  Found {total} records')
        
        migrated = 0
        skipped = 0
        errors = 0
        
        for obj in queryset.iterator(chunk_size=self.batch_size):
            self.stats['total_scanned'] += 1
            
            for file_field, url_field in field_mapping.items():
                result = self.migrate_field(obj, file_field, url_field, model_path)
                
                if result == 'migrated':
                    migrated += 1
                elif result == 'skipped':
                    skipped += 1
                elif result == 'error':
                    errors += 1
        
        self.stdout.write(f'  Migrated: {migrated}, Skipped: {skipped}, Errors: {errors}')
    
    def migrate_field(self, obj, file_field, url_field, model_path):
        """Migrate a single field from Cloudinary to local storage."""
        try:
            # Get the file field value
            file_value = getattr(obj, file_field, None)
            url_value = getattr(obj, url_field, None)
            
            # Determine the Cloudinary URL to download
            cloudinary_url = None
            
            # Check if file field has a Cloudinary URL
            if file_value:
                if hasattr(file_value, 'url'):
                    try:
                        cloudinary_url = file_value.url
                    except:
                        pass
                elif hasattr(file_value, 'build_url'):
                    try:
                        cloudinary_url = file_value.build_url(secure=True)
                    except:
                        pass
                elif isinstance(file_value, str) and file_value:
                    # It might be a public_id, construct URL
                    if 'cloudinary.com' not in file_value:
                        # Construct Cloudinary URL from public_id
                        cloud_name = self.get_cloudinary_cloud_name()
                        if cloud_name:
                            cloudinary_url = f'https://res.cloudinary.com/{cloud_name}/image/upload/{file_value}'
                    else:
                        cloudinary_url = file_value
            
            # If no URL from file field, check URL field
            if not cloudinary_url and url_value:
                if 'cloudinary.com' in str(url_value):
                    cloudinary_url = url_value
            
            # Skip if no Cloudinary URL found
            if not cloudinary_url or 'cloudinary.com' not in str(cloudinary_url):
                return 'skipped'
            
            # Ensure HTTPS
            if cloudinary_url.startswith('http://'):
                cloudinary_url = cloudinary_url.replace('http://', 'https://', 1)
            
            # Generate local filename and path
            local_filename = self.generate_local_filename(cloudinary_url, file_field)
            local_folder = self.get_local_folder(model_path, file_field)
            local_path = os.path.join(self.media_root, local_folder, local_filename)
            
            # Check if already exists locally
            if self.skip_existing and os.path.exists(local_path):
                # Update URL to local if not already
                local_url = self.build_local_url(local_folder, local_filename)
                if url_value != local_url:
                    if not self.dry_run:
                        setattr(obj, url_field, local_url)
                        obj.save(update_fields=[url_field])
                    self.stdout.write(f'    Updated URL (file exists): {obj.pk}')
                return 'skipped'
            
            # Log what we're doing
            self.stdout.write(f'    {obj.pk}: {cloudinary_url[:60]}...')
            
            if self.dry_run:
                self.stdout.write(self.style.NOTICE(f'      -> Would download to: {local_path}'))
                return 'migrated'
            
            # Download the file
            try:
                response = requests.get(cloudinary_url, timeout=30, stream=True)
                response.raise_for_status()
                
                # Get file size
                file_size = int(response.headers.get('content-length', 0))
                self.stats['total_bytes'] += file_size
                
                # Ensure directory exists
                os.makedirs(os.path.dirname(local_path), exist_ok=True)
                
                # Save file
                with open(local_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        f.write(chunk)
                
                self.stdout.write(self.style.SUCCESS(f'      Downloaded: {local_filename} ({file_size} bytes)'))
                
            except requests.RequestException as e:
                self.stdout.write(self.style.ERROR(f'      Download failed: {e}'))
                self.stats['total_errors'] += 1
                return 'error'
            
            # Build local URL
            local_url = self.build_local_url(local_folder, local_filename)
            
            # Update the URL field
            setattr(obj, url_field, local_url)
            obj.save(update_fields=[url_field])
            
            self.stdout.write(self.style.SUCCESS(f'      URL updated: {local_url}'))
            
            # Optionally delete from Cloudinary
            if self.delete_from_cloudinary:
                self.delete_cloudinary_file(file_value, cloudinary_url)
            
            self.stats['total_migrated'] += 1
            return 'migrated'
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'    Error processing {obj.pk}: {e}'))
            self.stats['total_errors'] += 1
            return 'error'
    
    def get_cloudinary_cloud_name(self):
        """Get Cloudinary cloud name from settings."""
        try:
            import cloudinary
            return cloudinary.config().cloud_name
        except:
            return None
    
    def generate_local_filename(self, url, field_name):
        """Generate a local filename from Cloudinary URL."""
        # Parse URL to get the path
        parsed = urlparse(url)
        path = unquote(parsed.path)
        
        # Extract filename from path
        # Cloudinary URLs: /cloud_name/image/upload/v123/folder/filename.ext
        parts = path.split('/')
        
        # Find the filename (last part)
        filename = parts[-1] if parts else 'unknown'
        
        # If filename has no extension, try to determine from URL
        if '.' not in filename:
            # Check for format in URL transformations
            if 'f_jpg' in url or 'f_jpeg' in url:
                filename += '.jpg'
            elif 'f_png' in url:
                filename += '.png'
            elif 'f_webp' in url:
                filename += '.webp'
            else:
                filename += '.jpg'  # Default to jpg
        
        # Ensure unique filename with timestamp
        base, ext = os.path.splitext(filename)
        # Clean the base name
        base = re.sub(r'[^\w\-]', '_', base)
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        unique_hash = hashlib.md5(url.encode()).hexdigest()[:8]
        
        return f'{base}_{unique_hash}{ext}'
    
    def get_local_folder(self, model_path, field_name):
        """Get local folder path for a model's files."""
        app_label, model_name = model_path.split('.')
        # Create organized folder structure
        folder = f'migrated/{app_label}/{model_name}/{field_name}'
        return folder
    
    def build_local_url(self, folder, filename):
        """Build the full URL for a local file.
        
        For local development: Uses SITE_URL if set (e.g., http://127.0.0.1:8000/media/...)
        For production: Uses SITE_URL (e.g., https://api.biochemknust.com/media/...)
        """
        # Build relative path
        relative_path = f'{folder}/{filename}'
        
        # Always build full URL with SITE_URL for consistency
        # This ensures the URLs work across different environments
        if self.site_url:
            full_url = f'{self.site_url.rstrip("/")}{self.media_url}{relative_path}'
        else:
            # If no SITE_URL, use relative path (for Vite proxy)
            full_url = f'{self.media_url}{relative_path}'
        
        return full_url
    
    def delete_cloudinary_file(self, file_value, url):
        """Delete a file from Cloudinary."""
        try:
            import cloudinary.uploader
            
            # Get public_id
            public_id = None
            if hasattr(file_value, 'public_id'):
                public_id = file_value.public_id
            elif hasattr(file_value, 'name'):
                public_id = file_value.name
            else:
                # Extract from URL
                match = re.search(r'/upload/(?:v\d+/)?(.+?)(?:\.[a-z]+)?$', url)
                if match:
                    public_id = match.group(1)
            
            if public_id:
                result = cloudinary.uploader.destroy(public_id)
                if result.get('result') == 'ok':
                    self.stdout.write(self.style.WARNING(f'      Deleted from Cloudinary: {public_id}'))
                else:
                    self.stdout.write(self.style.WARNING(f'      Cloudinary delete result: {result}'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'      Failed to delete from Cloudinary: {e}'))
    
    def print_summary(self):
        """Print migration summary."""
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('MIGRATION SUMMARY'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(f'Total records scanned: {self.stats["total_scanned"]}')
        self.stdout.write(self.style.SUCCESS(f'Files migrated: {self.stats["total_migrated"]}'))
        self.stdout.write(f'Files skipped: {self.stats["total_skipped"]}')
        self.stdout.write(self.style.ERROR(f'Errors: {self.stats["total_errors"]}'))
        self.stdout.write(f'Total bytes downloaded: {self.stats["total_bytes"]:,}')
        
        if self.dry_run:
            self.stdout.write('')
            self.stdout.write(self.style.NOTICE('This was a DRY RUN. No changes were made.'))
            self.stdout.write(self.style.NOTICE('Run without --dry-run to perform actual migration.'))
        else:
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Migration complete!'))
            self.stdout.write('')
            self.stdout.write('Next steps:')
            self.stdout.write('1. Set MEDIA_STORAGE_BACKEND = "local" in settings.py')
            self.stdout.write('2. Ensure MEDIA_ROOT and MEDIA_URL are properly configured')
            self.stdout.write('3. Configure your web server to serve files from MEDIA_ROOT')
