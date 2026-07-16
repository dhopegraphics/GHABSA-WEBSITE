"""
Django Management Command: Cleanup Abandoned Transactions
For PythonAnywhere - Run as daily scheduled task

Setup on PythonAnywhere:
1. Go to "Tasks" tab in your PythonAnywhere dashboard
2. Add a daily scheduled task (e.g., 3:00 AM)
3. Command: cd /home/yourusername/BIOCHEM-KNUST-Backend && python manage.py cleanup_abandoned_transactions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
import logging

from payments.models import Transaction

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Mark old pending transactions as failed/abandoned (PythonAnywhere compatible)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--hours',
            type=int,
            default=48,
            help='Mark transactions older than this many hours as abandoned (default: 48)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )

    def handle(self, *args, **options):
        hours = options['hours']
        dry_run = options['dry_run']

        self.stdout.write(self.style.NOTICE(
            f'\n{"="*60}\n'
            f'Cleanup Abandoned Transactions - {timezone.now()}\n'
            f'{"="*60}'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))

        cutoff_time = timezone.now() - timedelta(hours=hours)

        # Find abandoned transactions
        abandoned_transactions = Transaction.objects.filter(
            status='pending',
            initiated_at__lt=cutoff_time
        ).select_related('user', 'gateway')

        count = abandoned_transactions.count()

        if count == 0:
            self.stdout.write(self.style.SUCCESS(
                f'✓ No abandoned transactions found (older than {hours} hours)\n'
            ))
            return

        self.stdout.write(self.style.WARNING(
            f'Found {count} abandoned transaction(s) to mark as failed\n'
        ))

        for transaction in abandoned_transactions:
            self.stdout.write(f'\n{"-"*60}')
            self.stdout.write(f'Transaction: {transaction.reference}')
            self.stdout.write(f'User: {transaction.user.student_id if hasattr(transaction.user, "student_id") else transaction.user.email}')
            self.stdout.write(f'Amount: {transaction.currency.code} {transaction.amount}')
            self.stdout.write(f'Age: {timezone.now() - transaction.initiated_at}')

            if dry_run:
                self.stdout.write(self.style.WARNING('[DRY RUN] Would mark as failed'))
            else:
                transaction.status = 'failed'
                transaction.failure_reason = f'Transaction abandoned - exceeded {hours} hour timeout'
                transaction.status_message = 'Automatically marked as failed due to timeout'
                transaction.completed_at = timezone.now()
                transaction.save(update_fields=['status', 'failure_reason', 'status_message', 'completed_at'])
                self.stdout.write(self.style.ERROR('✗ Marked as failed'))

        if not dry_run:
            self.stdout.write(self.style.SUCCESS(
                f'\n✓ Marked {count} abandoned transaction(s) as failed\n'
            ))
            logger.info(f"Marked {count} abandoned transactions as failed")
        else:
            self.stdout.write(self.style.WARNING(
                f'\n[DRY RUN] Would mark {count} transaction(s) as failed\n'
            ))
