"""
Management command to find and fix successful transactions missing ProductPayment records

This handles the critical case where:
- Transaction status = 'success' (payment confirmed)
- BUT ProductPayment record was never created (customer has no validation code)

This can happen if:
1. complete_product_payment() threw an exception after transaction was marked success
2. Race condition between webhook and verify API
3. Database error during ProductPayment creation
4. Bug in complete_product_payment() code

Usage:
    python manage.py fix_orphaned_payments --dry-run  # See what would be fixed
    python manage.py fix_orphaned_payments  # Actually fix the orphaned payments
    python manage.py fix_orphaned_payments --reference TXN-XXX  # Fix specific transaction
    python manage.py fix_orphaned_payments --days 30  # Look back 30 days
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from django.db.models import Q
from django.contrib.contenttypes.models import ContentType
from payments.models import Transaction
from products.models import ProductPayment, Product
from products.payment_service import ProductPaymentService
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Find and fix successful transactions that are missing ProductPayment records'

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
            help='Specific transaction reference to fix',
        )
        parser.add_argument(
            '--reduce-stock',
            action='store_true',
            default=False,
            help='Also reduce stock (use with caution - stock may have been reduced already)',
        )
        parser.add_argument(
            '--send-notification',
            action='store_true',
            default=True,
            help='Send notification to user (default: True)',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days = options['days']
        specific_ref = options['reference']
        reduce_stock = options['reduce_stock']
        send_notification = options['send_notification']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN MODE - No changes will be made\n'))
        
        self.stdout.write(self.style.HTTP_INFO('\n' + '='*80))
        self.stdout.write(self.style.HTTP_INFO('🚨 ORPHANED PAYMENT RECOVERY TOOL'))
        self.stdout.write(self.style.HTTP_INFO('Finding successful transactions without ProductPayment records'))
        self.stdout.write(self.style.HTTP_INFO('='*80 + '\n'))
        
        if specific_ref:
            # Fix specific transaction
            try:
                transaction = Transaction.objects.get(reference=specific_ref)
                self.fix_single_transaction(transaction, dry_run, reduce_stock, send_notification)
            except Transaction.DoesNotExist:
                self.stdout.write(self.style.ERROR(f'❌ Transaction {specific_ref} not found'))
            return
        
        # Find all orphaned successful product payments
        cutoff = timezone.now() - timedelta(days=days)
        
        # Get the content type for Product
        product_content_type = ContentType.objects.get_for_model(Product)
        
        # Find successful transactions for products that don't have ProductPayment
        successful_transactions = Transaction.objects.filter(
            status='success',
            transaction_type='payment',
            content_type=product_content_type,
            initiated_at__gte=cutoff,
        ).order_by('-initiated_at')
        
        self.stdout.write(f'Checking {successful_transactions.count()} successful product transactions from last {days} days...\n')
        
        orphaned = []
        
        for transaction in successful_transactions:
            # Check if ProductPayment exists
            has_payment = ProductPayment.objects.filter(
                Q(transaction_record=transaction) | Q(reference=transaction.reference)
            ).exists()
            
            # Also check cart items if it's a cart checkout
            if not has_payment and transaction.metadata.get('cart_checkout'):
                # For cart checkouts, check if ANY item has ProductPayment
                cart_items = transaction.metadata.get('cart_items', [])
                for idx, _ in enumerate(cart_items):
                    if ProductPayment.objects.filter(reference__startswith=f"{transaction.reference}-{idx}").exists():
                        has_payment = True
                        break
            
            if not has_payment:
                orphaned.append(transaction)
        
        if not orphaned:
            self.stdout.write(self.style.SUCCESS(
                '✅ No orphaned payments found! All successful transactions have ProductPayment records.\n'
            ))
            return
        
        self.stdout.write(self.style.ERROR(
            f'🚨 FOUND {len(orphaned)} ORPHANED TRANSACTION(S)!\n'
            f'   These customers paid but never received validation codes!\n'
        ))
        
        fixed_count = 0
        error_count = 0
        
        for idx, transaction in enumerate(orphaned, 1):
            self.stdout.write(f'\n{"-"*60}')
            self.stdout.write(f'[{idx}/{len(orphaned)}] {transaction.reference}')
            self.stdout.write(f'   User: {transaction.user.get_full_name() if transaction.user else "N/A"} ({transaction.customer_phone})')
            self.stdout.write(f'   Amount: GHS {transaction.amount}')
            self.stdout.write(f'   Paid at: {transaction.completed_at or transaction.initiated_at}')
            
            # Show what products were purchased
            if transaction.metadata.get('cart_checkout'):
                items = transaction.metadata.get('items', [])
                self.stdout.write(f'   Items: {len(items)} item(s)')
                for item in items:
                    self.stdout.write(f'      - {item.get("product_name")} x{item.get("quantity")}')
            else:
                product_name = transaction.metadata.get('product_name', 'Unknown')
                quantity = transaction.metadata.get('quantity', 1)
                self.stdout.write(f'   Product: {product_name} x{quantity}')
            
            result = self.fix_single_transaction(transaction, dry_run, reduce_stock, send_notification)
            
            if result == 'fixed':
                fixed_count += 1
            elif result == 'error':
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*80)
        self.stdout.write(self.style.HTTP_INFO('RECOVERY SUMMARY'))
        self.stdout.write('='*80)
        self.stdout.write(f'🔍 Total orphaned found: {len(orphaned)}')
        self.stdout.write(self.style.SUCCESS(f'✅ Successfully fixed: {fixed_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Errors: {error_count}'))
        self.stdout.write('='*80 + '\n')

    def fix_single_transaction(self, transaction, dry_run=False, reduce_stock=False, send_notification=True):
        """
        Create ProductPayment for a successful transaction that's missing one
        
        Returns:
            'fixed': Successfully created ProductPayment
            'already_exists': ProductPayment already exists
            'error': Error occurred
            'not_success': Transaction is not successful
        """
        try:
            # Verify transaction is successful
            if transaction.status != 'success':
                self.stdout.write(self.style.WARNING(
                    f'   ⚠️  Transaction status is "{transaction.status}", not "success" - skipping'
                ))
                return 'not_success'
            
            # Check if ProductPayment already exists
            existing = ProductPayment.objects.filter(
                Q(transaction_record=transaction) | Q(reference=transaction.reference)
            ).first()
            
            if existing:
                self.stdout.write(self.style.WARNING(
                    f'   ⚠️  ProductPayment already exists: {existing.transaction_validation_code}'
                ))
                return 'already_exists'
            
            if dry_run:
                self.stdout.write(self.style.WARNING('   [DRY RUN] Would create ProductPayment'))
                return 'fixed'
            
            # Create ProductPayment using the service
            self.stdout.write('   🔧 Creating ProductPayment...')
            
            try:
                result = ProductPaymentService.complete_product_payment(
                    transaction=transaction,
                    reduce_stock=reduce_stock,
                    send_notification=send_notification,
                )
                
                validation_codes = result.get('validation_codes', [])
                
                self.stdout.write(self.style.SUCCESS('   ✅ ProductPayment created successfully!'))
                
                for vc in validation_codes:
                    if isinstance(vc, dict):
                        code = vc.get('code', 'N/A')
                        product = vc.get('product_name', 'Unknown')
                        self.stdout.write(self.style.SUCCESS(f'      💎 Code: {code} for {product}'))
                    else:
                        self.stdout.write(self.style.SUCCESS(f'      💎 Code: {vc}'))
                
                if send_notification:
                    self.stdout.write('   📱 Notification sent to user')
                
                return 'fixed'
                
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'   ❌ Error creating ProductPayment: {e}'))
                logger.exception(f'Error fixing orphaned payment {transaction.reference}')
                return 'error'
                
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'   ❌ Unexpected error: {e}'))
            logger.exception(f'Unexpected error fixing {transaction.reference}')
            return 'error'
