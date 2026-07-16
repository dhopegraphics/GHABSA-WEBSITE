"""
Management command to check and update pending transfers.

This command polls Paystack API for transfers that are stuck in 'processing' status
and updates them based on the actual transfer status.

Usage:
    # Run once manually
    python manage.py check_pending_transfers
    
    # Run with verbose output
    python manage.py check_pending_transfers --verbosity=2
    
    # Check transfers older than 1 hour (default is 5 minutes)
    python manage.py check_pending_transfers --min-age=60

For production, set up a cron job to run this every 5-10 minutes:
    */5 * * * * cd /path/to/project && python manage.py check_pending_transfers >> /var/log/transfers.log 2>&1
"""
import logging
from datetime import timedelta

from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q

from donations.models import DonationWithdrawal
from donations.services import DonationService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check pending/processing gateway transfers and update their status from Paystack'

    def add_arguments(self, parser):
        parser.add_argument(
            '--min-age',
            type=int,
            default=5,
            help='Minimum age in minutes of transfers to check (default: 5)'
        )
        parser.add_argument(
            '--max-age',
            type=int,
            default=1440,  # 24 hours
            help='Maximum age in minutes of transfers to check (default: 1440 = 24 hours)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Only check status, do not update database'
        )

    def handle(self, *args, **options):
        min_age = options['min_age']
        max_age = options['max_age']
        dry_run = options['dry_run']
        verbosity = options['verbosity']
        
        now = timezone.now()
        min_age_threshold = now - timedelta(minutes=min_age)
        max_age_threshold = now - timedelta(minutes=max_age)
        
        # Find processing/pending gateway transfers
        pending_withdrawals = DonationWithdrawal.objects.filter(
            Q(status='processing') | Q(status='approved'),
            transfer_method='gateway',
            gateway_transfer_code__isnull=False,
            created_at__lt=min_age_threshold,
            created_at__gt=max_age_threshold,
        ).exclude(
            gateway_transfer_code=''
        )
        
        count = pending_withdrawals.count()
        
        if verbosity >= 1:
            self.stdout.write(f"Found {count} pending gateway transfers to check")
        
        if count == 0:
            return
        
        updated = 0
        failed = 0
        still_pending = 0
        errors = 0
        
        for withdrawal in pending_withdrawals:
            if verbosity >= 2:
                self.stdout.write(f"\nChecking {withdrawal.reference} ({withdrawal.gateway_transfer_code})...")
            
            try:
                result = DonationService.verify_transfer(withdrawal.gateway_transfer_code)
                
                if result['success']:
                    transfer_status = result.get('transfer_status', '').lower()
                    
                    if verbosity >= 2:
                        self.stdout.write(f"  Paystack status: {transfer_status}")
                    
                    if transfer_status == 'success':
                        if not dry_run:
                            DonationService.complete_gateway_transfer(
                                withdrawal=withdrawal,
                                transfer_status='success',
                                gateway_data=result.get('details')
                            )
                        self.stdout.write(
                            self.style.SUCCESS(f"  ✓ {withdrawal.reference}: Completed!")
                        )
                        updated += 1
                        
                    elif transfer_status in ['failed', 'reversed']:
                        if not dry_run:
                            DonationService.complete_gateway_transfer(
                                withdrawal=withdrawal,
                                transfer_status='failed',
                                gateway_data=result.get('details')
                            )
                        self.stdout.write(
                            self.style.ERROR(f"  ✗ {withdrawal.reference}: {transfer_status}")
                        )
                        failed += 1
                        
                    elif transfer_status in ['pending', 'otp']:
                        still_pending += 1
                        if verbosity >= 2:
                            self.stdout.write(f"  ⏳ Still {transfer_status}")
                    
                    else:
                        still_pending += 1
                        if verbosity >= 2:
                            self.stdout.write(f"  ? Unknown status: {transfer_status}")
                else:
                    errors += 1
                    if verbosity >= 1:
                        self.stdout.write(
                            self.style.WARNING(f"  ! {withdrawal.reference}: {result.get('error', 'Unknown error')}")
                        )
                        
            except Exception as e:
                errors += 1
                logger.error(f"Error checking {withdrawal.reference}: {str(e)}")
                if verbosity >= 1:
                    self.stdout.write(
                        self.style.ERROR(f"  ! {withdrawal.reference}: Error - {str(e)}")
                    )
        
        # Summary
        if verbosity >= 1:
            self.stdout.write("\n" + "="*50)
            self.stdout.write(f"Summary:")
            self.stdout.write(f"  Completed: {updated}")
            self.stdout.write(f"  Failed/Reversed: {failed}")
            self.stdout.write(f"  Still pending: {still_pending}")
            self.stdout.write(f"  Errors: {errors}")
            
            if dry_run:
                self.stdout.write(self.style.WARNING("\n(Dry run - no changes made)"))
