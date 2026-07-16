"""
Management command to clean up expired pending payment registrations
Run this command periodically (e.g., via cron job) to automatically
remove registrations that haven't been paid within the timeout period
"""

from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from events.models import EventRegistration
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up expired pending payment registrations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=24,
            help='Number of hours after which pending payments expire (default: 24)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be deleted without actually deleting'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']
        
        # Calculate cutoff time
        cutoff_time = timezone.now() - timedelta(hours=hours)
        
        # Find expired pending payment registrations
        expired_registrations = EventRegistration.objects.filter(
            status='pending_payment',
            created_at__lt=cutoff_time
        )
        
        count = expired_registrations.count()
        
        if count == 0:
            self.stdout.write(
                self.style.SUCCESS('No expired registrations found.')
            )
            return
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING(f'DRY RUN: Would delete {count} expired registration(s):')
            )
            for reg in expired_registrations:
                self.stdout.write(
                    f'  - {reg.registration_number} ({reg.event.event_name}) '
                    f'by {reg.user.username} - Created: {reg.created_at}'
                )
        else:
            # Delete expired registrations
            deleted_count = 0
            for reg in expired_registrations:
                event_name = reg.event.event_name
                user_name = reg.user.username
                reg_number = reg.registration_number
                
                reg.delete()
                deleted_count += 1
                
                logger.info(
                    f'Deleted expired registration {reg_number} '
                    f'for {event_name} by {user_name}'
                )
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully deleted {deleted_count} expired registration(s).'
                )
            )