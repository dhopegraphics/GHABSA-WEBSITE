"""
Management command to populate default expense categories.
Usage: python manage.py populate_expense_categories
"""
from django.core.management.base import BaseCommand
from payments.models import ExpenseCategory


class Command(BaseCommand):
    help = 'Populate default expense categories for the expense management system'

    # Default categories with icons, colors, descriptions and budget limits
    DEFAULT_CATEGORIES = [
        {
            'name': 'Office Supplies',
            'icon': '📎',
            'color': '#6366f1',
            'description': 'Stationery, printing materials, and general office supplies',
            'budget_limit': 2000.00,
        },
        {
            'name': 'Events & Programs',
            'icon': '🎉',
            'color': '#8b5cf6',
            'description': 'Expenses for organizing events, seminars, workshops, and programs',
            'budget_limit': 10000.00,
        },
        {
            'name': 'Transportation & Logistics',
            'icon': '🚗',
            'color': '#f59e0b',
            'description': 'Travel, fuel, vehicle maintenance, and logistics costs',
            'budget_limit': 5000.00,
        },
        {
            'name': 'Food & Refreshments',
            'icon': '🍕',
            'color': '#ef4444',
            'description': 'Catering, snacks, and refreshments for meetings and events',
            'budget_limit': 3000.00,
        },
        {
            'name': 'Equipment & Technology',
            'icon': '💻',
            'color': '#3b82f6',
            'description': 'Computers, electronics, software licenses, and tech equipment',
            'budget_limit': 15000.00,
        },
        {
            'name': 'Utilities & Services',
            'icon': '💡',
            'color': '#10b981',
            'description': 'Internet, electricity, water, and other utility bills',
            'budget_limit': 2500.00,
        },
        {
            'name': 'Printing & Publications',
            'icon': '📄',
            'color': '#14b8a6',
            'description': 'Banners, flyers, posters, and publication materials',
            'budget_limit': 3500.00,
        },
        {
            'name': 'Maintenance & Repairs',
            'icon': '🔧',
            'color': '#64748b',
            'description': 'Repairs, maintenance, and upkeep of facilities and equipment',
            'budget_limit': 4000.00,
        },
        {
            'name': 'Welfare & Support',
            'icon': '❤️',
            'color': '#ec4899',
            'description': 'Student welfare, donations, and support activities',
            'budget_limit': 5000.00,
        },
        {
            'name': 'Sports & Recreation',
            'icon': '⚽',
            'color': '#22c55e',
            'description': 'Sports equipment, jerseys, tournaments, and recreational activities',
            'budget_limit': 6000.00,
        },
        {
            'name': 'Marketing & Publicity',
            'icon': '📢',
            'color': '#f97316',
            'description': 'Advertising, social media promotions, and publicity materials',
            'budget_limit': 2000.00,
        },
        {
            'name': 'Training & Development',
            'icon': '📚',
            'color': '#0ea5e9',
            'description': 'Workshops, training sessions, and skill development programs',
            'budget_limit': 4000.00,
        },
        {
            'name': 'Honoraria & Allowances',
            'icon': '💵',
            'color': '#84cc16',
            'description': 'Speaker fees, guest honoraria, and executive allowances',
            'budget_limit': 8000.00,
        },
        {
            'name': 'Miscellaneous',
            'icon': '📦',
            'color': '#a855f7',
            'description': 'Other expenses that do not fit into specific categories',
            'budget_limit': 1500.00,
        },
    ]

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing categories before populating',
        )
        parser.add_argument(
            '--update',
            action='store_true',
            help='Update existing categories with new values',
        )

    def handle(self, *args, **options):
        clear = options.get('clear', False)
        update = options.get('update', False)

        if clear:
            deleted_count, _ = ExpenseCategory.objects.all().delete()
            self.stdout.write(
                self.style.WARNING(f'Cleared {deleted_count} existing categories')
            )

        created_count = 0
        updated_count = 0
        skipped_count = 0

        for category_data in self.DEFAULT_CATEGORIES:
            name = category_data['name']
            
            existing = ExpenseCategory.objects.filter(name=name).first()
            
            if existing:
                if update:
                    # Update existing category
                    for key, value in category_data.items():
                        setattr(existing, key, value)
                    existing.save()
                    updated_count += 1
                    self.stdout.write(f'  ✏️  Updated: {existing}')
                else:
                    skipped_count += 1
                    self.stdout.write(f'  ⏭️  Skipped (exists): {name}')
            else:
                # Create new category
                category = ExpenseCategory.objects.create(**category_data)
                created_count += 1
                self.stdout.write(f'  ✅ Created: {category}')

        self.stdout.write('')
        self.stdout.write(self.style.SUCCESS(f'Done! Created: {created_count}, Updated: {updated_count}, Skipped: {skipped_count}'))
