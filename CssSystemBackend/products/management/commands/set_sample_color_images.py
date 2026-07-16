"""
Management command to set sample product-specific color images for testing
"""
from django.core.management.base import BaseCommand
from products.models import Product, ProductColor, ProductColorImage


class Command(BaseCommand):
    help = 'Set sample product-specific color images for testing the color-specific image feature'

    def handle(self, *args, **options):
        # Get the CSS T-Shirt product
        try:
            product = Product.objects.filter(product_name__icontains='shirt').first()
            if not product:
                self.stdout.write(self.style.ERROR('No shirt product found'))
                return
            
            self.stdout.write(f'Setting color images for: {product.product_name}')
            
            # Sample image URLs for different colors
            color_images = {
                'White': 'https://images.unsplash.com/photo-1521572163474-6864f9cf17ab?w=400',
                'Black': 'https://images.unsplash.com/photo-1503341504253-dff4815485f1?w=400',
                'Navy Blue': 'https://images.unsplash.com/photo-1556821840-3a63f95609a7?w=400',
                'Royal Blue': 'https://images.unsplash.com/photo-1489987707025-afc232f7ea0f?w=400',
                'Red': 'https://images.unsplash.com/photo-1583743814966-8936f5b7be1a?w=400',
            }
            
            created = 0
            updated = 0
            
            for color_name, image_url in color_images.items():
                try:
                    color = ProductColor.objects.get(name=color_name)
                    
                    # Check if product has this color
                    if not product.available_colors.filter(id=color.id).exists():
                        self.stdout.write(f'  Skipping {color_name} - not available for this product')
                        continue
                    
                    # Create or update ProductColorImage
                    color_image, created_flag = ProductColorImage.objects.get_or_create(
                        product=product,
                        color=color,
                        defaults={
                            'color_image_url': image_url,
                            'display_order': 0
                        }
                    )
                    
                    if created_flag:
                        self.stdout.write(self.style.SUCCESS(f'✓ Created image for {product.product_name} - {color_name}'))
                        created += 1
                    else:
                        if not color_image.color_image and not color_image.color_image_url:
                            color_image.color_image_url = image_url
                            color_image.save()
                            self.stdout.write(self.style.SUCCESS(f'✓ Updated image for {product.product_name} - {color_name}'))
                            updated += 1
                        else:
                            self.stdout.write(f'  {color_name} already has an image')
                    
                except ProductColor.DoesNotExist:
                    self.stdout.write(self.style.WARNING(f'✗ Color {color_name} not found'))
            
            self.stdout.write('\n' + '='*70)
            self.stdout.write(self.style.SUCCESS(f'Created: {created} | Updated: {updated}'))
            self.stdout.write('\nNow you can:')
            self.stdout.write('1. Go to Django Admin → Products → Edit CSS T-Shirt')
            self.stdout.write('2. Scroll down to "Color-Specific Images" section')
            self.stdout.write('3. Upload actual product images for each color OR update image URLs')
            self.stdout.write('4. Test frontend - clicking color swatches will change the product image')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error: {str(e)}'))
