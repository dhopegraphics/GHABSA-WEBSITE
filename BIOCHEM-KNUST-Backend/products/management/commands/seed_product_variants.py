"""
Management command to seed default product colors and sizes

Usage:
    python manage.py seed_product_variants
"""
from django.core.management.base import BaseCommand
from products.models import ProductColor, ProductSize


class Command(BaseCommand):
    help = 'Seed default product colors and sizes'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🎨 Seeding Product Colors...'))
        
        # Default colors
        colors_data = [
            {'name': 'Black', 'hex_code': '#000000', 'display_order': 1},
            {'name': 'White', 'hex_code': '#FFFFFF', 'display_order': 2},
            {'name': 'Navy Blue', 'hex_code': '#000080', 'display_order': 3},
            {'name': 'Royal Blue', 'hex_code': '#4169E1', 'display_order': 4},
            {'name': 'Red', 'hex_code': '#FF0000', 'display_order': 5},
            {'name': 'Maroon', 'hex_code': '#800000', 'display_order': 6},
            {'name': 'Gray', 'hex_code': '#808080', 'display_order': 7},
            {'name': 'Green', 'hex_code': '#008000', 'display_order': 8},
            {'name': 'Yellow', 'hex_code': '#FFFF00', 'display_order': 9},
            {'name': 'Orange', 'hex_code': '#FFA500', 'display_order': 10},
        ]
        
        colors_created = 0
        for color_data in colors_data:
            color, created = ProductColor.objects.get_or_create(
                name=color_data['name'],
                defaults={
                    'hex_code': color_data['hex_code'],
                    'display_order': color_data['display_order'],
                    'is_active': True,
                }
            )
            if created:
                colors_created += 1
                self.stdout.write(f'  ✓ Created: {color.name}')
            else:
                self.stdout.write(f'  - Exists: {color.name}')
        
        self.stdout.write(self.style.SUCCESS(f'\n📏 Seeding Product Sizes...'))
        
        # Default sizes
        sizes_data = [
            {'name': 'Extra Small', 'code': 'XS', 'display_order': 1},
            {'name': 'Small', 'code': 'S', 'display_order': 2},
            {'name': 'Medium', 'code': 'M', 'display_order': 3},
            {'name': 'Large', 'code': 'L', 'display_order': 4},
            {'name': 'Extra Large', 'code': 'XL', 'display_order': 5},
            {'name': 'Double Extra Large', 'code': 'XXL', 'display_order': 6},
            {'name': 'Triple Extra Large', 'code': 'XXXL', 'display_order': 7},
        ]
        
        sizes_created = 0
        for size_data in sizes_data:
            size, created = ProductSize.objects.get_or_create(
                code=size_data['code'],
                defaults={
                    'name': size_data['name'],
                    'display_order': size_data['display_order'],
                    'is_active': True,
                }
            )
            if created:
                sizes_created += 1
                self.stdout.write(f'  ✓ Created: {size.name} ({size.code})')
            else:
                self.stdout.write(f'  - Exists: {size.name} ({size.code})')
        
        self.stdout.write('\n' + '='*70)
        self.stdout.write(self.style.SUCCESS(f'\n✅ Done!'))
        self.stdout.write(f'   Colors created: {colors_created}/{len(colors_data)}')
        self.stdout.write(f'   Sizes created: {sizes_created}/{len(sizes_data)}')
        self.stdout.write(f'\n💡 You can now assign these to products in the admin panel')
