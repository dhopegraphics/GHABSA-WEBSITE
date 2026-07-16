"""
Management command to fix pending product payments
Verifies pending transactions with Paystack and completes successful ones

Usage:
    python manage.py fix_pending_payments
    python manage.py fix_pending_payments --dry-run  (to see what would be fixed)
    python manage.py fix_pending_payments --reference TXN-XXX  (fix specific transaction)
"""
from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from payments.models import Transaction
from payments.services.transaction_service import TransactionService
from products.payment_service import ProductPaymentService
from django.contrib.contenttypes.models import ContentType
from products.models import Product


class Command(BaseCommand):
    help = 'Fix pending product payments by verifying with Paystack and completing them'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be fixed without making changes',
        )
        parser.add_argument(
            '--reference',
            type=str,
            help='Fix specific transaction by reference',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=30,
            help='Check transactions from last N days (default: 30)',
        )
        parser.add_argument(
            '--skip-failed',
            action='store_true',
            help='Skip transactions that fail verification (instead of counting as errors)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        reference = options.get('reference')
        days = options['days']
        skip_failed = options.get('skip_failed', False)

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        if skip_failed:
            self.stdout.write(self.style.WARNING('⏭️  SKIP FAILED MODE - Unverifiable transactions will be skipped'))

        # Get product content type
        product_content_type = ContentType.objects.get_for_model(Product)

        # Query pending product transactions
        if reference:
            transactions = Transaction.objects.filter(
                reference=reference,
                content_type=product_content_type
            )
            self.stdout.write(f'🔍 Checking specific transaction: {reference}')
        else:
            from django.utils import timezone
            from datetime import timedelta
            
            cutoff_date = timezone.now() - timedelta(days=days)
            transactions = Transaction.objects.filter(
                status='pending',
                transaction_type='payment',
                content_type=product_content_type,
                initiated_at__gte=cutoff_date
            ).order_by('-initiated_at')
            
            self.stdout.write(f'🔍 Found {transactions.count()} pending product transactions from last {days} days')

        if not transactions.exists():
            self.stdout.write(self.style.SUCCESS('✅ No pending transactions to fix!'))
            return

        fixed_count = 0
        failed_count = 0
        skipped_count = 0
        already_success_count = 0
        payment_failed_count = 0

        for transaction in transactions:
            self.stdout.write(f'\n📦 Processing: {transaction.reference}')
            self.stdout.write(f'   Amount: GH₵{transaction.amount}')
            self.stdout.write(f'   Customer: {transaction.customer_name or transaction.customer_email}')
            self.stdout.write(f'   Date: {transaction.initiated_at}')
            
            try:
                # Check current status
                if transaction.status == 'success':
                    self.stdout.write(self.style.SUCCESS(f'   ✓ Already marked as success'))
                    already_success_count += 1
                    
                    # Still try to complete product payment if not done
                    if not transaction.merchandise_validation_code:
                        if not dry_run:
                            try:
                                result = ProductPaymentService.complete_product_payment(
                                    transaction=transaction,
                                    reduce_stock=True,
                                    send_notification=True,
                                )
                                self.stdout.write(self.style.SUCCESS(f'   ✓ Product payment completed'))
                                self.stdout.write(f'   📋 Validation Code: {transaction.merchandise_validation_code}')
                                fixed_count += 1
                            except Exception as e:
                                self.stdout.write(self.style.WARNING(f'   ⚠️  Failed to complete product payment: {str(e)}'))
                        else:
                            self.stdout.write(self.style.WARNING(f'   [DRY RUN] Would complete product payment'))
                    continue

                # Verify with Paystack
                self.stdout.write(f'   🔄 Verifying with Paystack...')
                
                if not dry_run:
                    verified_transaction = TransactionService.verify_payment(transaction.reference)
                    
                    if verified_transaction.status == 'success':
                        self.stdout.write(self.style.SUCCESS(f'   ✅ Payment verified as SUCCESSFUL'))
                        
                        # Complete product payment
                        try:
                            result = ProductPaymentService.complete_product_payment(
                                transaction=verified_transaction,
                                reduce_stock=True,
                                send_notification=True,
                            )
                            self.stdout.write(self.style.SUCCESS(f'   ✅ Product payment completed'))
                            self.stdout.write(f'   📋 Validation Code: {verified_transaction.merchandise_validation_code}')
                            self.stdout.write(f'   📧 SMS sent to: {verified_transaction.customer_phone}')
                            fixed_count += 1
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'   ❌ Failed to complete product payment: {str(e)}'))
                            failed_count += 1
                            
                    elif verified_transaction.status == 'failed':
                        self.stdout.write(self.style.WARNING(f'   ⚠️  Payment actually FAILED at gateway'))
                        payment_failed_count += 1
                    else:
                        self.stdout.write(self.style.WARNING(f'   ⚠️  Payment still pending at gateway'))
                        
                else:
                    # In dry run, try to peek at gateway status without updating
                    try:
                        gateway = TransactionService.get_gateway_instance(transaction.gateway.name)
                        result = gateway.verify_payment(transaction.reference)
                        
                        if result.get('status') == 'success':
                            self.stdout.write(self.style.SUCCESS(f'   [DRY RUN] Would mark as SUCCESS and complete'))
                            if hasattr(transaction.content_object, 'product_name'):
                                self.stdout.write(f'   [DRY RUN] Would reduce stock for: {transaction.content_object.product_name}')
                            self.stdout.write(f'   [DRY RUN] Would send SMS to: {transaction.customer_phone}')
                            fixed_count += 1
                        elif result.get('status') == 'failed':
                            self.stdout.write(self.style.WARNING(f'   [DRY RUN] Payment actually failed at gateway'))
                            payment_failed_count += 1
                        else:
                            self.stdout.write(self.style.WARNING(f'   [DRY RUN] Still pending at gateway'))
                    except Exception as e:
                        error_msg = str(e)
                        if 'NoneType' in error_msg and 'amount' in error_msg.lower():
                            self.stdout.write(self.style.WARNING(f'   [DRY RUN] Cannot verify - gateway returned incomplete data (possible old/orphaned transaction)'))
                            self.stdout.write(self.style.WARNING(f'   💡 Suggestion: Skip this transaction or manually verify with Paystack dashboard'))
                        else:
                            self.stdout.write(self.style.ERROR(f'   [DRY RUN] Verification failed: {error_msg}'))
                        
                        if skip_failed:
                            skipped_count += 1
                        else:
                            failed_count += 1

            except Exception as e:
                error_msg = str(e)
                if 'NoneType' in error_msg or 'incomplete data' in error_msg.lower():
                    self.stdout.write(self.style.WARNING(f'   ⚠️  Cannot verify - gateway returned incomplete data'))
                    if skip_failed:
                        self.stdout.write(self.style.WARNING(f'   ⏭️  Skipping...'))
                        skipped_count += 1
                    else:
                        self.stdout.write(self.style.ERROR(f'   ❌ Error: {error_msg}'))
                        failed_count += 1
                else:
                    self.stdout.write(self.style.ERROR(f'   ❌ Error: {error_msg}'))
                    failed_count += 1
                import traceback
                if options['verbosity'] >= 2:
                    traceback.print_exc()

        # Summary
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS('\n📊 SUMMARY:'))
        self.stdout.write(f'   Total checked: {transactions.count()}')
        self.stdout.write(self.style.SUCCESS(f'   ✅ Fixed/Completed: {fixed_count}'))
        self.stdout.write(self.style.WARNING(f'   ⚠️  Payment failed at gateway: {payment_failed_count}'))
        self.stdout.write(self.style.SUCCESS(f'   ✓ Already success: {already_success_count}'))
        if skipped_count > 0:
            self.stdout.write(self.style.WARNING(f'   ⏭️  Skipped (unverifiable): {skipped_count}'))
        self.stdout.write(self.style.ERROR(f'   ❌ Errors: {failed_count}'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n⚠️  This was a DRY RUN - no changes were made'))
            self.stdout.write('Run without --dry-run to apply fixes')
        else:
            self.stdout.write(self.style.SUCCESS('\n✅ Done! All pending payments have been processed.'))
