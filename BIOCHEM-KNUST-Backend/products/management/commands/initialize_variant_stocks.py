"""
Management command to initialize variant stocks for existing products.

Usage:
    python manage.py initialize_variant_stocks              # All products with variants
    python manage.py initialize_variant_stocks --product_id=<uuid>  # Specific product
    python manage.py initialize_variant_stocks --stock=10   # Set initial stock to 10
"""
from django.core.management.base import BaseCommand
from products.models import Product, ProductVariantStock


class Command(BaseCommand):
    help = 'Initialize variant stocks for products with colors/sizes'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--product_id',
            type=str,
            help='Initialize stocks for a specific product (UUID)',
        )
        parser.add_argument(
            '--stock',
            type=int,
            default=0,
            help='Initial stock quantity per variant (default: 0)',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating',
        )
    
    def handle(self, *args, **options):
        product_id = options.get('product_id')
        initial_stock = options.get('stock')
        dry_run = options.get('dry_run')
        
        if product_id:
            try:
                products = Product.objects.filter(product_id=product_id)
                if not products.exists():
                    self.stderr.write(self.style.ERROR(f'Product with ID {product_id} not found'))
                    return
            except Exception as e:
                self.stderr.write(self.style.ERROR(f'Invalid product ID: {e}'))
                return
        else:
            # Get all products with variants that don't have variant stocks yet
            products = Product.objects.filter(
                models.Q(has_colors=True) | models.Q(has_sizes=True)
            )
        
        total_created = 0
        
        for product in products:
            if not product.has_colors and not product.has_sizes:
                continue
            
            self.stdout.write(f'\n📦 Processing: {product.product_name}')
            self.stdout.write(f'   Colors: {product.available_colors.count() if product.has_colors else "N/A"}')
            self.stdout.write(f'   Sizes: {product.available_sizes.count() if product.has_sizes else "N/A"}')
            
            variants_to_create = []
            
            if product.has_colors and product.has_sizes:
                # Create stock entries for each color+size combination
                for color in product.available_colors.all():
                    for size in product.available_sizes.all():
                        exists = ProductVariantStock.objects.filter(
                            product=product, color=color, size=size
                        ).exists()
                        
                        if not exists:
                            variants_to_create.append({
                                'color': color,
                                'size': size,
                                'description': f'{color.name} / {size.code}'
                            })
            
            elif product.has_colors:
                for color in product.available_colors.all():
                    exists = ProductVariantStock.objects.filter(
                        product=product, color=color, size=None
                    ).exists()
                    
                    if not exists:
                        variants_to_create.append({
                            'color': color,
                            'size': None,
                            'description': f'{color.name}'
                        })
            
            elif product.has_sizes:
                for size in product.available_sizes.all():
                    exists = ProductVariantStock.objects.filter(
                        product=product, color=None, size=size
                    ).exists()
                    
                    if not exists:
                        variants_to_create.append({
                            'color': None,
                            'size': size,
                            'description': f'{size.code}'
                        })
            
            if variants_to_create:
                self.stdout.write(f'   Will create {len(variants_to_create)} variant stock(s):')
                for v in variants_to_create:
                    self.stdout.write(f'      - {v["description"]} (stock: {initial_stock})')
                
                if not dry_run:
                    for v in variants_to_create:
                        ProductVariantStock.objects.create(
                            product=product,
                            color=v['color'],
                            size=v['size'],
                            stock_quantity=initial_stock
                        )
                    total_created += len(variants_to_create)
                    self.stdout.write(self.style.SUCCESS(f'   ✅ Created {len(variants_to_create)} variant stocks'))
            else:
                self.stdout.write(self.style.WARNING(f'   ⏭️ All variant stocks already exist'))
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'\n🔍 DRY RUN - No changes made'))
        else:
            self.stdout.write(self.style.SUCCESS(f'\n✅ Total variant stocks created: {total_created}'))


# Import models at the top level for the filter
from django.db import models
