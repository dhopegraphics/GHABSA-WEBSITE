from django.core.management.base import BaseCommand
from products.models import Product, ProductColor, ProductSize


class Command(BaseCommand):
    help = 'Enable variants (colors/sizes) on a product'

    def add_arguments(self, parser):
        parser.add_argument(
            '--product-id',
            type=str,
            help='Product ID (UUID)',
        )
        parser.add_argument(
            '--product-name',
            type=str,
            help='Product name (partial match)',
        )
        parser.add_argument(
            '--enable-colors',
            action='store_true',
            help='Enable color variants',
        )
        parser.add_argument(
            '--enable-sizes',
            action='store_true',
            help='Enable size variants',
        )
        parser.add_argument(
            '--all-colors',
            action='store_true',
            help='Assign all active colors',
        )
        parser.add_argument(
            '--all-sizes',
            action='store_true',
            help='Assign all active sizes',
        )
        parser.add_argument(
            '--list',
            action='store_true',
            help='List all products',
        )

    def handle(self, *args, **options):
        if options.get('list'):
            self.list_products()
            return

        product_id = options.get('product_id')
        product_name = options.get('product_name')
        enable_colors = options.get('enable_colors')
        enable_sizes = options.get('enable_sizes')
        all_colors = options.get('all_colors')
        all_sizes = options.get('all_sizes')

        if not product_id and not product_name:
            self.stdout.write(self.style.ERROR('Please provide --product-id or --product-name'))
            return

        # Find product
        try:
            if product_id:
                product = Product.objects.get(product_id=product_id)
            else:
                products = Product.objects.filter(product_name__icontains=product_name)
                if products.count() == 0:
                    self.stdout.write(self.style.ERROR(f'No products found matching "{product_name}"'))
                    return
                elif products.count() > 1:
                    self.stdout.write(self.style.WARNING(f'Multiple products found:'))
                    for p in products:
                        self.stdout.write(f'  - {p.product_name} ({p.product_id})')
                    self.stdout.write('\nPlease use --product-id to specify exactly which one')
                    return
                product = products.first()

            self.stdout.write(f'\n📦 Product: {product.product_name}')
            self.stdout.write(f'   ID: {product.product_id}')
            self.stdout.write(f'   Current state:')
            self.stdout.write(f'     - has_colors: {product.has_colors}')
            self.stdout.write(f'     - has_sizes: {product.has_sizes}')
            self.stdout.write(f'     - Colors assigned: {product.available_colors.count()}')
            self.stdout.write(f'     - Sizes assigned: {product.available_sizes.count()}')

            # Enable colors
            if enable_colors:
                product.has_colors = True
                self.stdout.write(self.style.SUCCESS('\n✅ Enabled color variants'))

            # Enable sizes
            if enable_sizes:
                product.has_sizes = True
                self.stdout.write(self.style.SUCCESS('✅ Enabled size variants'))

            # Assign all colors
            if all_colors:
                colors = ProductColor.objects.filter(is_active=True)
                product.available_colors.set(colors)
                self.stdout.write(self.style.SUCCESS(f'✅ Assigned {colors.count()} colors'))
                for color in colors:
                    self.stdout.write(f'   - {color.name} ({color.hex_code})')

            # Assign all sizes
            if all_sizes:
                sizes = ProductSize.objects.filter(is_active=True)
                product.available_sizes.set(sizes)
                self.stdout.write(self.style.SUCCESS(f'✅ Assigned {sizes.count()} sizes'))
                for size in sizes:
                    self.stdout.write(f'   - {size.name} ({size.code})')

            product.save()
            self.stdout.write(self.style.SUCCESS(f'\n✨ Product updated successfully!'))

            # Show final state
            self.stdout.write(f'\n📊 Final state:')
            self.stdout.write(f'   - has_colors: {product.has_colors}')
            self.stdout.write(f'   - has_sizes: {product.has_sizes}')
            self.stdout.write(f'   - Colors available: {product.available_colors.count()}')
            self.stdout.write(f'   - Sizes available: {product.available_sizes.count()}')

        except Product.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'Product not found: {product_id}'))

    def list_products(self):
        products = Product.objects.all().order_by('-created_at')
        self.stdout.write(self.style.SUCCESS(f'\n📦 All Products ({products.count()})\n'))
        
        for product in products:
            self.stdout.write('=' * 80)
            self.stdout.write(f'Name: {product.product_name}')
            self.stdout.write(f'ID: {product.product_id}')
            self.stdout.write(f'Type: {product.type_of_product}')
            self.stdout.write(f'Price: GH₵{product.price}')
            self.stdout.write(f'Stock: {product.stock_quantity}')
            
            variant_status = []
            if product.has_colors:
                variant_status.append(f'✅ Colors ({product.available_colors.count()})')
            else:
                variant_status.append('❌ Colors')
            
            if product.has_sizes:
                variant_status.append(f'✅ Sizes ({product.available_sizes.count()})')
            else:
                variant_status.append('❌ Sizes')
            
            self.stdout.write(f'Variants: {" | ".join(variant_status)}')
            self.stdout.write('')
