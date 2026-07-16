"""
Data Migration Script: ProductPayment to Transaction
Migrates existing ProductPayment records to the new integrated Transaction system

This script should be run AFTER the database migrations are applied.
"""
from django.core.management.base import BaseCommand
from django.db import transaction as db_transaction
from django.contrib.contenttypes.models import ContentType
from django.utils import timezone
from decimal import Decimal

from products.models import Product, ProductPayment
from payments.models import Transaction, Currency, PaymentGateway


class Command(BaseCommand):
    help = 'Migrate ProductPayment data to Transaction model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run migration in dry-run mode (no changes)',
        )
        parser.add_argument(
            '--batch-size',
            type=int,
            default=100,
            help='Number of records to process per batch',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        batch_size = options['batch_size']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('Running in DRY-RUN mode (no changes will be made)'))
        
        # Get default currency and gateway
        try:
            currency = Currency.objects.get(code='GHS')
        except Currency.DoesNotExist:
            self.stdout.write(self.style.ERROR('GHS currency not found. Please create it first.'))
            return
        
        try:
            gateway = PaymentGateway.objects.get(name='paystack')
        except PaymentGateway.DoesNotExist:
            self.stdout.write(self.style.ERROR('Paystack gateway not found. Please create it first.'))
            return
        
        # Get Product content type
        product_content_type = ContentType.objects.get_for_model(Product)
        
        # Get all ProductPayment records
        old_payments = ProductPayment.objects.select_related('product').all()
        total_count = old_payments.count()
        
        if total_count == 0:
            self.stdout.write(self.style.SUCCESS('No ProductPayment records to migrate'))
            return
        
        self.stdout.write(f'Found {total_count} ProductPayment records to migrate')
        
        migrated_count = 0
        skipped_count = 0
        error_count = 0
        
        for payment in old_payments:
            try:
                # Check if already migrated (by reference)
                if payment.reference and Transaction.objects.filter(reference=payment.reference).exists():
                    self.stdout.write(f'  Skipping {payment.reference} (already migrated)')
                    skipped_count += 1
                    continue
                
                if dry_run:
                    self.stdout.write(f'  Would migrate: {payment.transaction_validation_code} -> Transaction')
                    migrated_count += 1
                    continue
                
                # Create Transaction record
                with db_transaction.atomic():
                    transaction = Transaction.objects.create(
                        # Basic info
                        reference=payment.reference or f'MIGRATED-{payment.payment_id}',
                        user=None,  # ProductPayment doesn't have user field
                        transaction_type='payment',
                        amount=payment.product.price if payment.product else Decimal('0.00'),
                        currency=currency,
                        gateway=gateway,
                        
                        # Status
                        status='success' if payment.payment_successful else 'failed',
                        status_message='Migrated from ProductPayment',
                        
                        # Content object (product)
                        content_type=product_content_type,
                        object_id=str(payment.product.product_id) if payment.product else None,
                        
                        # Description
                        description=f'Purchase of {payment.product.product_name}' if payment.product else 'Product purchase',
                        
                        # Fees (calculated based on gateway)
                        gateway_fee=gateway.calculate_fee(payment.product.price) if payment.product else Decimal('0.00'),
                        platform_fee=Decimal('0.00'),
                        net_amount=payment.product.price if payment.product else Decimal('0.00'),
                        
                        # Payment details
                        payment_method='paystack',
                        payment_channel='',
                        
                        # Gateway response
                        gateway_reference=payment.transaction,
                        gateway_response='',
                        gateway_metadata={'migrated': True, 'old_payment_id': str(payment.payment_id)},
                        
                        # Customer info
                        customer_email='',
                        customer_phone=str(payment.phone) if payment.phone else '',
                        customer_name='',
                        
                        # Timestamps
                        initiated_at=payment.payed_at,
                        completed_at=payment.payed_at if payment.payment_successful else None,
                        
                        # Metadata
                        metadata={
                            'product_id': str(payment.product.product_id) if payment.product else None,
                            'product_name': payment.product.product_name if payment.product else 'Unknown',
                            'quantity': 1,
                            'migrated_from': 'ProductPayment',
                            'old_payment_id': str(payment.payment_id),
                        },
                        
                        # Merchandise tracking
                        merchandise_validation_code=payment.transaction_validation_code,
                        merchandise_collected=payment.merchandise_taken,
                        merchandise_collected_at=None,  # Old model doesn't have this
                    )
                    
                    # Calculate net amount after fees
                    transaction.net_amount = transaction.amount - transaction.gateway_fee - transaction.platform_fee
                    transaction.save()
                    
                    migrated_count += 1
                    self.stdout.write(
                        self.style.SUCCESS(
                            f'  ✓ Migrated: {payment.transaction_validation_code} -> {transaction.reference}'
                        )
                    )
            
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(
                        f'  ✗ Error migrating {payment.transaction_validation_code}: {str(e)}'
                    )
                )
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'Migration Summary:'))
        self.stdout.write(f'  Total records: {total_count}')
        self.stdout.write(self.style.SUCCESS(f'  Migrated: {migrated_count}'))
        self.stdout.write(self.style.WARNING(f'  Skipped: {skipped_count}'))
        self.stdout.write(self.style.ERROR(f'  Errors: {error_count}'))
        
        if dry_run:
            self.stdout.write('\n' + self.style.WARNING('DRY-RUN completed. Run without --dry-run to apply changes.'))
        else:
            self.stdout.write('\n' + self.style.SUCCESS('Migration completed!'))
            self.stdout.write(
                self.style.WARNING(
                    '\nNote: Old ProductPayment records have been preserved. '
                    'You can safely delete them after verifying the migration.'
                )
            )
