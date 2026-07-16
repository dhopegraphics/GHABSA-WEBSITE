"""
Django Management Command: Retry Pending Transactions
For PythonAnywhere - Run as scheduled task every 5-10 minutes

Setup on PythonAnywhere:
1. Go to "Tasks" tab in your PythonAnywhere dashboard
2. Add a scheduled task
3. Set it to run every 5 or 10 minutes (hourly on free accounts)
4. Command: cd /home/yourusername/BIOCHEM-KNUST-Backend && python manage.py retry_pending_transactions
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db import transaction as db_transaction
from datetime import timedelta
import logging

from payments.models import Transaction
from payments.services.transaction_service import TransactionService
from products.payment_service import ProductPaymentService

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Check and retry pending transactions (PythonAnywhere compatible)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--max-age-hours',
            type=int,
            default=24,
            help='Maximum age of pending transactions to check (default: 24 hours)'
        )
        parser.add_argument(
            '--min-age-minutes',
            type=int,
            default=5,
            help='Minimum age of pending transactions to check (default: 5 minutes)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it'
        )

    def handle(self, *args, **options):
        max_age_hours = options['max_age_hours']
        min_age_minutes = options['min_age_minutes']
        dry_run = options['dry_run']

        self.stdout.write(self.style.NOTICE(
            f'\n{"="*60}\n'
            f'Retry Pending Transactions - {timezone.now()}\n'
            f'{"="*60}'
        ))

        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))

        now = timezone.now()
        min_age = now - timedelta(minutes=min_age_minutes)
        max_age = now - timedelta(hours=max_age_hours)

        # Find pending transactions
        pending_transactions = Transaction.objects.filter(
            status='pending',
            initiated_at__gte=max_age,
            initiated_at__lte=min_age
        ).select_related('gateway', 'user').order_by('initiated_at')

        total_count = pending_transactions.count()

        if total_count == 0:
            self.stdout.write(self.style.SUCCESS(
                '✓ No pending transactions to retry\n'
            ))
            return

        self.stdout.write(self.style.WARNING(
            f'Found {total_count} pending transaction(s) to retry\n'
        ))

        success_count = 0
        failed_count = 0
        already_completed = 0

        for transaction in pending_transactions:
            self.stdout.write(f'\n{"-"*60}')
            self.stdout.write(f'Transaction: {transaction.reference}')
            self.stdout.write(f'User: {transaction.user.student_id if hasattr(transaction.user, "student_id") else transaction.user.email}')
            self.stdout.write(f'Amount: {transaction.currency.code} {transaction.amount}')
            self.stdout.write(f'Age: {now - transaction.initiated_at}')

            if dry_run:
                self.stdout.write(self.style.WARNING('[DRY RUN] Would retry verification'))
                continue

            try:
                # Check current status first (may have been updated by webhook)
                transaction.refresh_from_db()
                if transaction.status != 'pending':
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ Already {transaction.status} (updated elsewhere)'
                    ))
                    already_completed += 1
                    continue

                # Check if ProductPayment already exists (transaction may be stuck as pending but actually complete)
                from products.models import ProductPayment
                existing_payment = ProductPayment.objects.filter(transaction_record=transaction).first()
                if existing_payment:
                    self.stdout.write(self.style.SUCCESS(
                        f'✓ ProductPayment exists - marking transaction as success'
                    ))
                    transaction.status = 'success'
                    transaction.completed_at = timezone.now()
                    transaction.status_message = 'Synced with existing ProductPayment'
                    transaction.save(update_fields=['status', 'completed_at', 'status_message'])
                    already_completed += 1
                    continue

                # Try to verify with payment gateway
                self.stdout.write('Verifying with payment gateway...')
                
                try:
                    result = TransactionService.verify_payment(
                        reference=transaction.reference
                    )

                    # Result is the updated transaction object
                    if result.status == 'success':
                        transaction_obj = result

                        # If it's a product payment, complete the product purchase
                        if transaction_obj.transaction_type == 'payment':
                            try:
                                completion_result = ProductPaymentService.complete_product_payment(
                                    transaction=transaction_obj,
                                    reduce_stock=True,
                                    send_notification=True
                                )

                                validation_codes = completion_result.get('validation_codes', [])
                                self.stdout.write(self.style.SUCCESS(
                                    f'✅ Transaction verified and completed!\n'
                                    f'   Validation codes: {[vc.get("code") for vc in validation_codes]}'
                                ))
                                success_count += 1
                            except Exception as e:
                                self.stdout.write(self.style.ERROR(
                                    f'✗ Transaction verified but product completion failed: {str(e)}'
                                ))
                                logger.exception(f'Product completion failed for {transaction.reference}')
                                failed_count += 1
                        else:
                            self.stdout.write(self.style.SUCCESS(
                                '✓ Transaction verified (non-product payment)'
                            ))
                            success_count += 1
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'⚠ Verification returned status: {result.status} - will retry later'
                        ))
                        # Don't mark as failed yet - leave as pending for another retry
                        failed_count += 1
                        
                except Exception as e:
                    error_msg = str(e)
                    
                    # Check if this is a Paystack 400 error (invalid reference)
                    if '400' in error_msg and 'Bad Request' in error_msg:
                        self.stdout.write(self.style.WARNING(
                            f'⚠ Paystack doesn\'t recognize reference - this may need manual recovery\n'
                            f'   Check Paystack dashboard to see if payment actually succeeded'
                        ))
                        # Don't mark as failed yet - could be a reference mismatch issue
                        # Will be handled by the 48-hour cleanup if not resolved
                        logger.warning(
                            f'Paystack 400 error for {transaction.reference}. '
                            f'User: {transaction.user.student_id if hasattr(transaction.user, "student_id") else transaction.user.email}. '
                            f'Amount: {transaction.amount}. '
                            f'This may need manual recovery.'
                        )
                    else:
                        # Other errors (network issues, timeouts, etc.) - just log and retry later
                        self.stdout.write(self.style.WARNING(
                            f'⚠ Verification error (will retry later): {error_msg[:100]}'
                        ))
                        logger.error(f'Verification error for {transaction.reference}: {error_msg}')
                    
                    failed_count += 1

            except Exception as e:
                logger.exception(f'Unexpected error retrying transaction {transaction.reference}')
                self.stdout.write(self.style.ERROR(
                    f'✗ Unexpected error: {str(e)}'
                ))
                failed_count += 1

        # Summary
        self.stdout.write(f'\n{"="*60}')
        self.stdout.write(self.style.NOTICE('PENDING TRANSACTIONS SUMMARY'))
        self.stdout.write(f'{"="*60}')
        self.stdout.write(f'Total pending: {total_count}')
        self.stdout.write(self.style.SUCCESS(f'Successfully completed: {success_count}'))
        if already_completed > 0:
            self.stdout.write(self.style.SUCCESS(f'Already completed: {already_completed}'))
        if failed_count > 0:
            self.stdout.write(self.style.ERROR(f'Failed: {failed_count}'))
        self.stdout.write(f'{"="*60}\n')

        # =============================================================
        # CRITICAL: Check for orphaned successful transactions
        # These are transactions marked 'success' but missing ProductPayment
        # =============================================================
        self.stdout.write(self.style.NOTICE(
            f'\n{"="*60}\n'
            f'Checking for orphaned successful transactions...\n'
            f'{"="*60}'
        ))
        
        from products.models import ProductPayment
        from django.contrib.contenttypes.models import ContentType
        from products.models import Product
        from django.db.models import Q
        
        product_content_type = ContentType.objects.get_for_model(Product)
        
        # Find successful transactions from last 24 hours
        orphan_cutoff = now - timedelta(hours=max_age_hours)
        successful_transactions = Transaction.objects.filter(
            status='success',
            transaction_type='payment',
            content_type=product_content_type,
            initiated_at__gte=orphan_cutoff,
        ).order_by('-initiated_at')
        
        orphaned_count = 0
        orphaned_fixed = 0
        
        for transaction in successful_transactions:
            # Check if ProductPayment exists
            has_payment = ProductPayment.objects.filter(
                Q(transaction_record=transaction) | Q(reference=transaction.reference)
            ).exists()
            
            # Also check cart items
            if not has_payment and transaction.metadata.get('cart_checkout'):
                cart_items = transaction.metadata.get('cart_items', [])
                for idx, _ in enumerate(cart_items):
                    if ProductPayment.objects.filter(reference__startswith=f"{transaction.reference}-{idx}").exists():
                        has_payment = True
                        break
            
            if not has_payment:
                orphaned_count += 1
                self.stdout.write(self.style.ERROR(
                    f'🚨 ORPHANED: {transaction.reference} - User: {transaction.customer_phone} - GHS {transaction.amount}'
                ))
                
                if not dry_run:
                    try:
                        result = ProductPaymentService.complete_product_payment(
                            transaction=transaction,
                            reduce_stock=False,  # Stock was likely reduced already
                            send_notification=True,
                        )
                        validation_codes = result.get('validation_codes', [])
                        self.stdout.write(self.style.SUCCESS(
                            f'   ✅ FIXED! Validation codes: {[vc.get("code") if isinstance(vc, dict) else vc for vc in validation_codes]}'
                        ))
                        orphaned_fixed += 1
                    except Exception as e:
                        self.stdout.write(self.style.ERROR(f'   ❌ Failed to fix: {e}'))
                else:
                    self.stdout.write(self.style.WARNING('   [DRY RUN] Would create ProductPayment'))
        
        if orphaned_count == 0:
            self.stdout.write(self.style.SUCCESS('✅ No orphaned successful transactions found'))
        else:
            self.stdout.write(f'\n🚨 Found {orphaned_count} orphaned transaction(s)')
            if not dry_run:
                self.stdout.write(self.style.SUCCESS(f'✅ Fixed {orphaned_fixed} orphaned transaction(s)'))

        # Cleanup old pending transactions (mark as abandoned after 48 hours)
        cleanup_cutoff = now - timedelta(hours=48)
        abandoned = Transaction.objects.filter(
            status='pending',
            initiated_at__lt=cleanup_cutoff
        )
        abandoned_count = abandoned.count()

        if abandoned_count > 0:
            if not dry_run:
                # Log each abandoned transaction for manual review
                for txn in abandoned[:10]:  # Log first 10
                    logger.warning(
                        f'Abandoning transaction {txn.reference} after 48 hours. '
                        f'User: {txn.user.student_id if hasattr(txn.user, "student_id") else txn.customer_email}. '
                        f'Amount: {txn.amount}. '
                        f'CHECK PAYSTACK DASHBOARD to confirm this actually failed!'
                    )
                
                abandoned.update(
                    status='failed',
                    status_message='Transaction timeout - exceeded 48 hours. Check Paystack dashboard to verify.',
                    completed_at=now
                )
                self.stdout.write(self.style.WARNING(
                    f'⚠️  Marked {abandoned_count} old transaction(s) as failed (48+ hours old)\n'
                    f'   IMPORTANT: Check Paystack dashboard to verify these actually failed!'
                ))
            else:
                self.stdout.write(self.style.WARNING(
                    f'[DRY RUN] Would mark {abandoned_count} old transaction(s) as failed (48+ hours)\n'
                ))
