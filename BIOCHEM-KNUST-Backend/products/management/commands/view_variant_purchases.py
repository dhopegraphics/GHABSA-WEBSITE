from django.core.management.base import BaseCommand
from payments.models import Transaction
from products.models import Product
import json


class Command(BaseCommand):
    help = 'View all product purchases with variant preferences'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reference',
            type=str,
            help='View specific transaction by reference',
        )
        parser.add_argument(
            '--user-id',
            type=str,
            help='Filter by user ID',
        )
        parser.add_argument(
            '--product-id',
            type=str,
            help='Filter by product ID',
        )

    def handle(self, *args, **options):
        reference = options.get('reference')
        user_id = options.get('user_id')
        product_id = options.get('product_id')

        # Build query
        transactions = Transaction.objects.filter(
            transaction_type='payment',
            status='success'
        ).select_related('user', 'content_type')

        if reference:
            transactions = transactions.filter(reference=reference)
        
        if user_id:
            transactions = transactions.filter(user_id=user_id)
        
        if product_id:
            # Filter by product through generic relation
            from django.contrib.contenttypes.models import ContentType
            product_ct = ContentType.objects.get_for_model(Product)
            transactions = transactions.filter(
                content_type=product_ct,
                object_id=product_id
            )

        # Display results
        self.stdout.write(self.style.SUCCESS(f'\nFound {transactions.count()} product purchases\n'))

        for txn in transactions.order_by('-initiated_at'):
            self.stdout.write('=' * 80)
            self.stdout.write(f'Reference: {txn.reference}')
            self.stdout.write(f'User: {txn.user.get_full_name()} ({txn.user.email})')
            self.stdout.write(f'Status: {txn.status}')
            self.stdout.write(f'Amount: GH₵{txn.amount}')
            self.stdout.write(f'Date: {txn.initiated_at}')
            
            # Product details
            if txn.content_object:
                product = txn.content_object
                self.stdout.write(f'\nProduct: {product.product_name}')
                self.stdout.write(f'Product ID: {product.product_id}')
                self.stdout.write(f'Has Colors: {product.has_colors}')
                self.stdout.write(f'Has Sizes: {product.has_sizes}')
            
            # Quantity
            quantity = txn.metadata.get('quantity', 1)
            self.stdout.write(f'Quantity: {quantity}')
            
            # Variant preferences
            variant_selections = txn.metadata.get('variant_selections', [])
            
            if variant_selections:
                self.stdout.write(self.style.SUCCESS('\n✅ VARIANT PREFERENCES:'))
                for idx, selection in enumerate(variant_selections, 1):
                    color_name = selection.get('color', {}).get('name', 'N/A')
                    size_code = selection.get('size', {}).get('code', 'N/A')
                    sel_quantity = selection.get('quantity', 1)
                    self.stdout.write(f'  Item {idx}: Color: {color_name}, Size: {size_code}, Qty: {sel_quantity}')
            else:
                self.stdout.write(self.style.WARNING('\n⚠️  No variant preferences set'))
            
            # Merchandise collection status
            if hasattr(txn, 'merchandise_collected'):
                if txn.merchandise_collected:
                    self.stdout.write(self.style.SUCCESS(f'\n✅ Collected on: {txn.merchandise_collected_at}'))
                else:
                    self.stdout.write(f'\n📦 Validation Code: {txn.merchandise_validation_code}')
                    self.stdout.write(self.style.WARNING('⏳ Pending collection'))
            
            self.stdout.write('')

        # Summary
        self.stdout.write('=' * 80)
        with_variants = sum(1 for t in transactions if t.metadata.get('variant_selections'))
        without_variants = transactions.count() - with_variants
        
        self.stdout.write(self.style.SUCCESS(f'\nSummary:'))
        self.stdout.write(f'  Total purchases: {transactions.count()}')
        self.stdout.write(f'  With variant preferences: {with_variants}')
        self.stdout.write(f'  Without variant preferences: {without_variants}')
        self.stdout.write('')
