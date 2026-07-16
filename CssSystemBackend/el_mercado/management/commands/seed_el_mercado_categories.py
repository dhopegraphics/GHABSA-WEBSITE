"""
Django management command to seed El Mercado categories
Usage: python manage.py seed_el_mercado_categories
"""

from django.core.management.base import BaseCommand
from el_mercado.seed_categories import seed_categories


class Command(BaseCommand):
    help = 'Seed El Mercado marketplace categories'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('🚀 Seeding El Mercado categories...'))
        
        try:
            count = seed_categories()
            self.stdout.write(
                self.style.SUCCESS(f'✅ Successfully seeded {count} categories!')
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error seeding categories: {str(e)}')
            )
