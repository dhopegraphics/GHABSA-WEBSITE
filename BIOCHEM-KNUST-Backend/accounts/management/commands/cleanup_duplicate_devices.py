"""
Management command to clean up duplicate device records

This command identifies and consolidates duplicate device records for users.
Duplicates occur when the old fingerprinting algorithm (which included IP address)
created new records for the same physical device on different networks.

Usage:
    python manage.py cleanup_duplicate_devices --dry-run  # Preview changes
    python manage.py cleanup_duplicate_devices            # Execute cleanup
    python manage.py cleanup_duplicate_devices --user-phone +233597959032  # Specific user
"""
from django.core.management.base import BaseCommand, CommandError
from django.db.models import Count, Min, Max
from django.utils import timezone
from accounts.device_models import UserDevice, DeviceLoginHistory
from accounts.models import CustomUser
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Clean up duplicate device records created by the old fingerprinting algorithm'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without making any modifications',
        )
        parser.add_argument(
            '--user-phone',
            type=str,
            help='Clean up devices for a specific user phone number (e.g., +233597959032)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed information about each device being processed',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        user_phone = options.get('user_phone')
        verbose = options['verbose']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))
        
        # Get users to process
        if user_phone:
            try:
                users = CustomUser.objects.filter(phone=user_phone)
                if not users.exists():
                    raise CommandError(f'No user found with phone: {user_phone}')
                self.stdout.write(f'Processing user: {user_phone}\n')
            except Exception as e:
                raise CommandError(f'Error finding user: {e}')
        else:
            # Get all users with multiple devices
            users_with_devices = UserDevice.objects.values('user').annotate(
                device_count=Count('id')
            ).filter(device_count__gt=1).values_list('user', flat=True)
            
            users = CustomUser.objects.filter(id__in=users_with_devices)
            self.stdout.write(f'Found {users.count()} users with multiple devices\n')
        
        total_duplicates_found = 0
        total_devices_deleted = 0
        total_users_processed = 0
        
        for user in users:
            duplicates, deleted = self.process_user_devices(user, dry_run, verbose)
            total_duplicates_found += duplicates
            total_devices_deleted += deleted
            if duplicates > 0:
                total_users_processed += 1
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('📊 CLEANUP SUMMARY'))
        self.stdout.write('='*60)
        self.stdout.write(f'Users processed with duplicates: {total_users_processed}')
        self.stdout.write(f'Duplicate device groups found: {total_duplicates_found}')
        self.stdout.write(f'Device records {"would be" if dry_run else ""} deleted: {total_devices_deleted}')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  This was a dry run. Run without --dry-run to apply changes.'))

    def process_user_devices(self, user, dry_run, verbose):
        """
        Process devices for a single user and identify duplicates.
        
        Duplicates are identified by:
        1. Same platform AND device_type AND device_name
        2. Or same platform AND device_type for mobile devices (iOS/Android)
        """
        devices = UserDevice.objects.filter(user=user).order_by('-last_active')
        
        if verbose:
            self.stdout.write(f'\n👤 User: {user.phone} - {user.get_full_name()}')
            self.stdout.write(f'   Total devices: {devices.count()}')
        
        # Group devices by characteristics
        device_groups = {}
        
        for device in devices:
            # Create a grouping key based on device characteristics
            # For mobile: platform + device_type + device_name (if available)
            # For web: platform + device_type + browser (simplified)
            
            if device.platform in ('ios', 'android'):
                # Mobile devices - group by platform + type + name
                key = (
                    device.platform,
                    device.device_type,
                    device.device_name or 'unknown'
                )
            else:
                # Web/Desktop - group by platform + type + browser family
                browser_family = device.browser.split()[0] if device.browser else 'unknown'
                key = (
                    device.platform,
                    device.device_type,
                    browser_family
                )
            
            if key not in device_groups:
                device_groups[key] = []
            device_groups[key].append(device)
        
        duplicates_found = 0
        devices_deleted = 0
        
        for key, group_devices in device_groups.items():
            if len(group_devices) > 1:
                duplicates_found += 1
                
                if verbose:
                    self.stdout.write(f'\n   📱 Duplicate group: {key}')
                    self.stdout.write(f'      Found {len(group_devices)} duplicate devices')
                
                # Keep the most recently active device (first in the list since we ordered by -last_active)
                keep_device = group_devices[0]
                duplicate_devices = group_devices[1:]
                
                # Also consider: keep trusted devices, keep the one with most login history
                for device in group_devices:
                    if device.is_trusted and not keep_device.is_trusted:
                        # Swap - prefer trusted device
                        duplicate_devices.remove(device)
                        duplicate_devices.append(keep_device)
                        keep_device = device
                
                if verbose:
                    self.stdout.write(f'      Keeping: {keep_device.get_device_display()} (ID: {str(keep_device.id)[:8]}...)')
                    self.stdout.write(f'         Last active: {keep_device.last_active}')
                    self.stdout.write(f'         Trusted: {keep_device.is_trusted}')
                
                # Merge data from duplicates to the kept device
                if not dry_run:
                    # Update first_login to the earliest among all duplicates
                    earliest_login = min(d.first_login for d in group_devices)
                    if keep_device.first_login > earliest_login:
                        keep_device.first_login = earliest_login
                    
                    # Transfer login history to kept device
                    for dup_device in duplicate_devices:
                        DeviceLoginHistory.objects.filter(device=dup_device).update(device=keep_device)
                    
                    keep_device.save()
                
                # Delete duplicates
                for dup_device in duplicate_devices:
                    devices_deleted += 1
                    if verbose:
                        self.stdout.write(
                            self.style.WARNING(
                                f'      Deleting: {dup_device.get_device_display()} '
                                f'(ID: {str(dup_device.id)[:8]}..., Last: {dup_device.last_active})'
                            )
                        )
                    
                    if not dry_run:
                        dup_device.delete()
        
        return duplicates_found, devices_deleted
