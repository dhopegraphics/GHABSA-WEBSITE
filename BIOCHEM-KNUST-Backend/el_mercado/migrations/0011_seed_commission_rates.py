# Generated data migration for seeding commission rates

from django.db import migrations
from decimal import Decimal


def seed_commission_rates(apps, schema_editor):
    """Seed initial commission rates"""
    CommissionRate = apps.get_model('el_mercado', 'CommissionRate')
    
    rates = [
        {
            'category_type': 'STANDARD',
            'rate': Decimal('5.00'),
            'description': 'Most physical products and goods - Electronics, Clothing, Books, Accessories, Home goods',
        },
        {
            'category_type': 'DIGITAL',
            'rate': Decimal('10.00'),
            'description': 'Digital downloads and software - E-books, Software, Templates, Digital art, Online courses',
        },
        {
            'category_type': 'SERVICES',
            'rate': Decimal('7.00'),
            'description': 'Professional and personal services - Tutoring, Graphic design, Writing, Consulting, Repairs',
        },
        {
            'category_type': 'HANDMADE',
            'rate': Decimal('4.00'),
            'description': 'Handcrafted and custom-made items - Art, Jewelry, Custom clothing, Crafts, Personalized items',
        },
    ]
    
    for rate_data in rates:
        CommissionRate.objects.get_or_create(
            category_type=rate_data['category_type'],
            defaults={
                'rate': rate_data['rate'],
                'description': rate_data['description'],
                'is_active': True,
            }
        )


def reverse_seed(apps, schema_editor):
    """Remove seeded commission rates"""
    CommissionRate = apps.get_model('el_mercado', 'CommissionRate')
    CommissionRate.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('el_mercado', '0010_commissionrate_and_more'),
    ]

    operations = [
        migrations.RunPython(seed_commission_rates, reverse_seed),
    ]
