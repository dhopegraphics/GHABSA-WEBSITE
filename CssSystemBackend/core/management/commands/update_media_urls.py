"""
Django Management Command: Update Media URLs

Updates all media URL fields to use the correct SITE_URL.
Run this after deploying to production or when changing domains.

Usage:
    python manage.py update_media_urls
    python manage.py update_media_urls --site-url=https://api.biochemknust.com
    python manage.py update_media_urls --dry-run
"""

import re
from django.core.management.base import BaseCommand
from django.conf import settings
from django.apps import apps


class Command(BaseCommand):
    help = 'Update all media URLs to use the correct SITE_URL'
    
    # Models and their URL fields
    URL_FIELDS_BY_MODEL = {
        'faculty.Staff': ['image_url'],
        'academics.Lecturer': ['profile_image_url'],
        'academics.AcademicSlides': ['file_url'],
        'academics.PastQuestions': ['file_url'],
        'academics.InternshipOpportunities': ['image_url'],
        'products.Product': ['product_image_url'],
        'products.ProductColorImage': ['color_image_url'],
        'donations.DonationWithdrawal': ['receipt_image_url'],
        'planner.TaskAttachment': ['file_url'],
        'projects.Project': ['image_url', 'image2_url', 'image3_url'],
        'voting.VotingEvent': ['banner_image_url'],
        'voting.Candidate': ['profile_image_url'],
        'voting.PollOption': ['image_url'],
        'codequest.CodeQuestProject': ['app_logo_url'],
        'codequest.CodeQuestConsultant': ['profile_image_url'],
        'news.News': ['head_image_url', 'back_image_url'],
        'admissions.AdmissionGuideline': ['image_url'],
        'history.SocietyHistory': ['image_url'],
        'history.HistoricalLeader': ['image_url'],
        'executives.Executive': ['image_url'],
        'executives.Appointee': ['image_url'],
        'advertisements.Advertisement': ['flyer_url'],
        'events.Event': ['event_image_1_url', 'event_image_2_url'],
        'events.SyncMemoAlbum': ['cover_photo_url'],
        'events.SyncMemoPhoto': ['photo_url'],
        'timeline.Timeline': ['image_url'],
        'helpdesk.RequestImage': ['image_url', 'thumbnail_url'],
    }
    
    # Pattern to match local media URLs
    LOCAL_MEDIA_PATTERN = re.compile(
        r'^(https?://)?'  # Optional protocol
        r'(localhost|127\.0\.0\.1|[a-zA-Z0-9.-]+)?'  # Optional host
        r'(:\d+)?'  # Optional port
        r'(/media/.+)$'  # Media path (captured)
    )
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--site-url',
            type=str,
            help='Override SITE_URL from settings (e.g., https://api.biochemknust.com)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without updating database',
        )
    
    def handle(self, *args, **options):
        self.dry_run = options['dry_run']
        
        # Get target SITE_URL
        self.site_url = options['site_url'] or getattr(settings, 'SITE_URL', '')
        
        if not self.site_url:
            self.stderr.write(self.style.ERROR(
                'SITE_URL not set! Use --site-url=https://your-domain.com or set SITE_URL in settings/env'
            ))
            return
        
        # Remove trailing slash
        self.site_url = self.site_url.rstrip('/')
        
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.WARNING('UPDATE MEDIA URLS'))
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(f'Target SITE_URL: {self.site_url}')
        
        if self.dry_run:
            self.stdout.write(self.style.NOTICE('\n>>> DRY RUN - No changes will be made <<<\n'))
        
        total_updated = 0
        total_skipped = 0
        
        for model_path, url_fields in self.URL_FIELDS_BY_MODEL.items():
            try:
                app_label, model_name = model_path.split('.')
                Model = apps.get_model(app_label, model_name)
            except Exception as e:
                continue  # Model doesn't exist, skip
            
            for url_field in url_fields:
                try:
                    # Get all records with a URL in this field
                    filter_kwargs = {f'{url_field}__isnull': False}
                    exclude_kwargs = {url_field: ''}
                    records = Model.objects.filter(**filter_kwargs).exclude(**exclude_kwargs)
                    
                    for record in records:
                        old_url = getattr(record, url_field, None)
                        if not old_url:
                            continue
                        
                        # Extract the /media/... path
                        match = self.LOCAL_MEDIA_PATTERN.match(old_url)
                        if match:
                            media_path = match.group(4)  # The /media/... part
                            new_url = f'{self.site_url}{media_path}'
                            
                            if old_url != new_url:
                                if not self.dry_run:
                                    setattr(record, url_field, new_url)
                                    record.save(update_fields=[url_field])
                                
                                self.stdout.write(
                                    f'  {model_name}.{url_field}: {old_url[:40]}... -> {new_url[:40]}...'
                                )
                                total_updated += 1
                            else:
                                total_skipped += 1
                        elif '/media/' in old_url:
                            # URL has media path but doesn't match pattern
                            # Try to extract just the media path
                            media_idx = old_url.find('/media/')
                            if media_idx >= 0:
                                media_path = old_url[media_idx:]
                                new_url = f'{self.site_url}{media_path}'
                                
                                if old_url != new_url:
                                    if not self.dry_run:
                                        setattr(record, url_field, new_url)
                                        record.save(update_fields=[url_field])
                                    
                                    self.stdout.write(
                                        f'  {model_name}.{url_field}: {old_url[:40]}... -> {new_url[:40]}...'
                                    )
                                    total_updated += 1
                                else:
                                    total_skipped += 1
                        else:
                            total_skipped += 1
                            
                except Exception as e:
                    self.stderr.write(f'  Error processing {model_path}.{url_field}: {e}')
        
        self.stdout.write('')
        self.stdout.write(self.style.WARNING('=' * 60))
        self.stdout.write(self.style.SUCCESS(f'URLs updated: {total_updated}'))
        self.stdout.write(f'URLs skipped (already correct or external): {total_skipped}')
        
        if self.dry_run:
            self.stdout.write(self.style.NOTICE('\nThis was a DRY RUN. Run without --dry-run to apply changes.'))
        else:
            self.stdout.write(self.style.SUCCESS('\nDone! All media URLs updated.'))
