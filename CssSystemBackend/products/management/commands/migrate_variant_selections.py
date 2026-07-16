"""
Management command to migrate variant selections from Transaction.metadata to ProductPayment.variant_selections
"""
from django.core.management.base import BaseCommand
from django.db import transaction
from payments.models import Transaction
from products.models import ProductPayment


class Command(BaseCommand):
    help = 'Migrate variant selections from Transaction metadata to ProductPayment model'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without actually doing it',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN MODE - No changes will be made\n'))
        
        # Find transactions with variant selections in metadata
        transactions = Transaction.objects.filter(
            status='success',
            metadata__variant_selections__isnull=False
        ).exclude(metadata__variant_selections=[])
        
        total = transactions.count()
        self.stdout.write(f'Found {total} transactions with variant selections in metadata\n')
        
        if total == 0:
            self.stdout.write(self.style.SUCCESS('No transactions need migration'))
            return
        
        migrated = 0
        linked = 0
        errors = 0
        
        for txn in transactions:
            try:
                # Get metadata variant selections (formatted with names)
                metadata_variants = txn.metadata.get('variant_selections', [])
                
                if not metadata_variants:
                    continue
                
                # Extract raw IDs from formatted data
                raw_selections = []
                for variant in metadata_variants:
                    selection = {
                        'quantity': variant.get('quantity', 1)
                    }
                    
                    # Extract color ID
                    if 'color' in variant and isinstance(variant['color'], dict):
                        selection['color_id'] = variant['color'].get('id')
                    
                    # Extract size ID
                    if 'size' in variant and isinstance(variant['size'], dict):
                        selection['size_id'] = variant['size'].get('id')
                    
                    raw_selections.append(selection)
                
                self.stdout.write(f'Transaction {txn.reference}:')
                self.stdout.write(f'  Extracted: {raw_selections}')
                
                # Find corresponding ProductPayment
                try:
                    product_payment = ProductPayment.objects.get(reference=txn.reference)
                    
                    if not dry_run:
                        with transaction.atomic():
                            # Update variant selections
                            product_payment.variant_selections = raw_selections
                            
                            # Link to transaction if not already linked
                            if not product_payment.transaction_record:
                                product_payment.transaction_record = txn
                                linked += 1
                                self.stdout.write(self.style.SUCCESS(f'  ✓ Linked to Transaction'))
                            
                            product_payment.save()
                            
                            # Also update Transaction.variant_selections for consistency
                            txn.variant_selections = raw_selections
                            txn.save(update_fields=['variant_selections'])
                    
                    migrated += 1
                    self.stdout.write(self.style.SUCCESS(f'  ✓ Migrated to ProductPayment {product_payment.payment_id}\n'))
                    
                except ProductPayment.DoesNotExist:
                    self.stdout.write(self.style.ERROR(f'  ✗ ProductPayment not found for {txn.reference}\n'))
                    errors += 1
                    
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'  ✗ Error: {str(e)}\n'))
                errors += 1
        
        # Summary
        self.stdout.write('\n' + '='*50)
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN COMPLETE - No changes made'))
        else:
            self.stdout.write(self.style.SUCCESS('MIGRATION COMPLETE'))
        
        self.stdout.write(f'Total transactions found: {total}')
        self.stdout.write(self.style.SUCCESS(f'Successfully migrated: {migrated}'))
        self.stdout.write(f'ProductPayments linked: {linked}')
        
        if errors > 0:
            self.stdout.write(self.style.ERROR(f'Errors: {errors}'))
        
        if not dry_run:
            self.stdout.write(self.style.SUCCESS('\n✓ All variant selections migrated to ProductPayment model'))
