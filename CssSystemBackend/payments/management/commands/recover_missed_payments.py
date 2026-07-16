"""
Management command to recover missed payments that succeeded on Paystack but failed in our system

Usage:
    python manage.py recover_missed_payments --dry-run  # Test mode, no changes
    python manage.py recover_missed_payments  # Actually recover payments
    python manage.py recover_missed_payments --reference TXN-XXX  # Recover specific transaction
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from payments.models import Transaction
from payments.services.transaction_service import TransactionService
from products.payment_service import ProductPaymentService
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Recover payments that succeeded on Paystack but are marked as failed in our system'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run in test mode without making any changes',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days to look back (default: 7)',
        )
        parser.add_argument(
            '--reference',
            type=str,
            help='Specific transaction reference to recover',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']
        specific_ref = options['reference']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made'))
        
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*80))
        self.stdout.write(self.style.HTTP_INFO('PAYMENT RECOVERY TOOL'))
        self.stdout.write(self.style.HTTP_INFO('='*80 + '\n'))
        
        if specific_ref:
            # Recover specific transaction
            try:
                transaction = Transaction.objects.get(reference=specific_ref)
                self.recover_single_transaction(transaction, dry_run)
            except Transaction.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Transaction {specific_ref} not found'))
        else:
            # Find all potentially missed payments
            cutoff = timezone.now() - timedelta(days=days)
            
            failed_transactions = Transaction.objects.filter(
                status='failed',
                initiated_at__gte=cutoff,
                transaction_type='payment',
                status_message__icontains='abandoned'
            ).order_by('-initiated_at')
            
            self.stdout.write(f'Found {failed_transactions.count()} potentially affected transactions\n')
            
            recovered_count = 0
            actually_failed_count = 0
            error_count = 0
            
            for idx, transaction in enumerate(failed_transactions, 1):
                self.stdout.write(f'\n[{idx}/{failed_transactions.count()}] Checking {transaction.reference}...')
                
                result = self.recover_single_transaction(transaction, dry_run)
                
                if result == 'recovered':
                    recovered_count += 1
                elif result == 'actually_failed':
                    actually_failed_count += 1
                elif result == 'error':
                    error_count += 1
            
            # Summary
            self.stdout.write('\n' + '='*80)
            self.stdout.write(self.style.SUCCESS('RECOVERY SUMMARY'))
            self.stdout.write('='*80)
            self.stdout.write(f'✅ Successfully Recovered: {recovered_count}')
            self.stdout.write(f'⚠️  Actually Failed on Paystack: {actually_failed_count}')
            self.stdout.write(f'❌ Errors: {error_count}')
            self.stdout.write('='*80 + '\n')
    
    def recover_single_transaction(self, transaction, dry_run=False):
        """
        Attempt to recover a single transaction
        
        Returns:
            'recovered': Successfully recovered
            'actually_failed': Actually failed on Paystack (not recoverable)
            'error': Error occurred
            'already_complete': Already has ProductPayment
        """
        try:
            # Check if already has ProductPayment
            from products.models import ProductPayment
            existing = ProductPayment.objects.filter(transaction_record=transaction).exists()
            
            if existing:
                self.stdout.write(self.style.WARNING('  ⚠️  Already has ProductPayment - skipping'))
                return 'already_complete'
            
            # Try to verify with Paystack
            try:
                self.stdout.write('  🔍 Verifying with Paystack...')
                
                # Use gateway_reference for verification
                verify_reference = transaction.gateway_reference if transaction.gateway_reference else transaction.reference
                
                # Get payment gateway and verify
                from payments.services.paystack_gateway import PaystackGateway
                gateway = PaystackGateway(transaction.gateway)
                
                paystack_result = gateway.verify_payment(verify_reference)
                
                if paystack_result.get('status') == 'success':
                    self.stdout.write(self.style.SUCCESS(f'  ✅ FOUND SUCCESS ON PAYSTACK!'))
                    self.stdout.write(f'     Amount: GHS {paystack_result.get("amount")}')
                    self.stdout.write(f'     Paid at: {paystack_result.get("paid_at")}')
                    self.stdout.write(f'     Channel: {paystack_result.get("channel")}')
                    
                    if not dry_run:
                        # Update transaction to success
                        transaction.status = 'success'
                        transaction.payment_channel = paystack_result.get('channel', 'unknown')
                        transaction.gateway_fee = paystack_result.get('fees', 0)
                        transaction.net_amount = transaction.amount - transaction.gateway_fee
                        transaction.completed_at = timezone.now()
                        transaction.status_message = 'Recovered via manual verification'
                        transaction.gateway_response = str(paystack_result)
                        transaction.save()
                        
                        # Complete product payment
                        try:
                            result = ProductPaymentService.complete_product_payment(
                                transaction=transaction,
                                reduce_stock=True,
                                send_notification=True
                            )
                            
                            validation_codes = result.get('validation_codes', [])
                            self.stdout.write(self.style.SUCCESS(f'  ✅ Product payment completed!'))
                            for vc in validation_codes:
                                self.stdout.write(f'     💎 Validation Code: {vc.get("code")} for {vc.get("product_name")}')
                            
                            return 'recovered'
                        except Exception as e:
                            self.stdout.write(self.style.ERROR(f'  ❌ Error completing product payment: {e}'))
                            return 'error'
                    else:
                        self.stdout.write(self.style.WARNING('  [DRY RUN] Would recover this transaction'))
                        return 'recovered'
                else:
                    self.stdout.write(self.style.WARNING(f'  ⚠️  Actually failed on Paystack: {paystack_result.get("message")}'))
                    return 'actually_failed'
                    
            except Exception as e:
                # Paystack verification failed - might be truly abandoned
                self.stdout.write(self.style.WARNING(f'  ⚠️  Paystack verification error: {str(e)[:100]}'))
                return 'actually_failed'
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'  ❌ Error: {e}'))
            logger.exception(f'Error recovering transaction {transaction.reference}')
            return 'error'
