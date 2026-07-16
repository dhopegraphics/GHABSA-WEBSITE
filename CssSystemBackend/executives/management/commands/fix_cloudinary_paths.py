"""
Management command to fix old Cloudinary paths in the database.

This command:
1. Finds records with old Cloudinary paths (image/upload/v.../...)
2. Matches them to migrated files in /media/migrated/...
3. Updates the image_url field with the correct local URL
4. Clears the invalid image field path

Usage:
    python manage.py fix_cloudinary_paths --dry-run  # Preview changes
    python manage.py fix_cloudinary_paths            # Apply changes
"""

import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import models
from django.apps import apps


class Command(BaseCommand):
    help = 'Fix old Cloudinary paths in database by mapping to migrated files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without applying them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made\n'))
        
        SITE_URL = getattr(settings, 'SITE_URL', '')
        MEDIA_URL = getattr(settings, 'MEDIA_URL', '/media/')
        
        if not SITE_URL:
            self.stdout.write(self.style.ERROR('ERROR: SITE_URL is not set in settings!'))
            self.stdout.write('Set SITE_URL in .env (e.g., SITE_URL=https://api.biochemknust.com)')
            return
        
        self.stdout.write(f'SITE_URL: {SITE_URL}')
        self.stdout.write(f'MEDIA_URL: {MEDIA_URL}\n')
        
        # Define models and their field mappings
        # Format: (app_label, model_name, file_field, url_field, migrated_path)
        MODEL_MAPPINGS = [
            ('executives', 'Appointee', 'image', 'image_url', 'migrated/executives/Appointee/image'),
            ('executives', 'Executive', 'image', 'image_url', 'migrated/executives/Executive/image'),
            ('events', 'Event', 'event_image_1', 'event_image_1_url', 'migrated/events/Event/event_image_1'),
            ('events', 'Event', 'event_image_2', 'event_image_2_url', 'migrated/events/Event/event_image_2'),
            ('news', 'News', 'head_image', 'head_image_url', 'migrated/news/News/head_image'),
            ('news', 'News', 'back_image', 'back_image_url', 'migrated/news/News/back_image'),
            ('products', 'Product', 'product_image', 'product_image_url', 'migrated/products/Product/product_image'),
            ('products', 'ProductColorImage', 'color_image', 'color_image_url', 'migrated/products/ProductColorImage/color_image'),
            ('academics', 'InternshipOpportunities', 'image', 'image_url', 'migrated/academics/InternshipOpportunities/image'),
            ('academics', 'Lecturer', 'profile_image', 'profile_image_url', 'migrated/academics/Lecturer/profile_image'),
        ]
        
        total_updated = 0
        total_cleared = 0
        
        for app_label, model_name, file_field, url_field, migrated_path in MODEL_MAPPINGS:
            try:
                model = apps.get_model(app_label, model_name)
            except LookupError:
                self.stdout.write(f'  Model {app_label}.{model_name} not found, skipping')
                continue
            
            # Build migrated files index
            migrated_dir = os.path.join(settings.MEDIA_ROOT, migrated_path)
            migrated_files = {}
            
            if os.path.exists(migrated_dir):
                for f in os.listdir(migrated_dir):
                    # Extract public_id from filename (format: publicid_hash.ext)
                    parts = f.rsplit('_', 1)
                    if len(parts) == 2:
                        public_id = parts[0]
                        migrated_files[public_id] = f
            
            # Find records with old Cloudinary paths
            filter_kwargs = {f'{file_field}__contains': 'image/upload/'}
            old_records = model.objects.filter(**filter_kwargs)
            count = old_records.count()
            
            if count == 0:
                continue
            
            self.stdout.write(f'\n{app_label}.{model_name}.{file_field}: {count} records with old paths')
            self.stdout.write(f'  Migrated files available: {len(migrated_files)}')
            
            updated = 0
            cleared = 0
            not_found = []
            
            for obj in old_records:
                field_value = getattr(obj, file_field)
                if not field_value:
                    continue
                
                old_path = str(field_value.name)
                # Extract public_id from path like: image/upload/v1764306675/AppointeeImages/onk7abfrt3yqccippt3o.jpg
                filename = os.path.basename(old_path)
                public_id = os.path.splitext(filename)[0]
                
                if public_id in migrated_files:
                    migrated_filename = migrated_files[public_id]
                    relative_path = f'{migrated_path}/{migrated_filename}'
                    full_url = f'{SITE_URL}{MEDIA_URL}{relative_path}'
                    
                    if not dry_run:
                        setattr(obj, url_field, full_url)
                        setattr(obj, file_field, '')
                        obj.save(update_fields=[file_field, url_field])
                    
                    updated += 1
                    self.stdout.write(f'    ✓ {public_id} → {full_url[:60]}...')
                else:
                    # No migrated file found, just clear the invalid path
                    if not dry_run:
                        setattr(obj, file_field, '')
                        obj.save(update_fields=[file_field])
                    
                    cleared += 1
                    not_found.append(public_id)
            
            self.stdout.write(f'  Updated: {updated}, Cleared (no file): {cleared}')
            if not_found:
                self.stdout.write(f'  Not found: {", ".join(not_found[:5])}{"..." if len(not_found) > 5 else ""}')
            
            total_updated += updated
            total_cleared += cleared
        
        self.stdout.write('\n' + '=' * 50)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN COMPLETE'))
            self.stdout.write(f'Would update: {total_updated} records')
            self.stdout.write(f'Would clear: {total_cleared} records')
            self.stdout.write('\nRun without --dry-run to apply changes')
        else:
            self.stdout.write(self.style.SUCCESS(f'DONE!'))
            self.stdout.write(f'Updated: {total_updated} records')
            self.stdout.write(f'Cleared: {total_cleared} records')
