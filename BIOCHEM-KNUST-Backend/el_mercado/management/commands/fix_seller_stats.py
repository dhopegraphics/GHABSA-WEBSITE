"""
Management command to recalculate and fix seller statistics.
Usage: python manage.py fix_seller_stats
"""
from django.core.management.base import BaseCommand
from django.db.models import Count
from el_mercado.models import Seller, MarketplaceOrder


class Command(BaseCommand):
    help = 'Recalculate and fix seller statistics (total_sales)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('Fixing seller statistics...'))
        
        sellers = Seller.objects.all()
        fixed_count = 0
        
        for seller in sellers:
            # Count actual completed orders
            completed_orders = MarketplaceOrder.objects.filter(
                seller=seller,
                status='COMPLETED'
            ).count()
            
            # Check if needs update
            if seller.total_sales != completed_orders:
                old_value = seller.total_sales
                seller.total_sales = completed_orders
                seller.save(update_fields=['total_sales'])
                
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✅ {seller.display_name}: {old_value} → {completed_orders}'
                    )
                )
                fixed_count += 1
        
        if fixed_count == 0:
            self.stdout.write(self.style.SUCCESS('All seller stats are correct!'))
        else:
            self.stdout.write(
                self.style.SUCCESS(f'\n✅ Fixed {fixed_count} seller(s)')
            )
