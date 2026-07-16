"""
Management command to backfill ProductAudit with historical price changes
based on existing ProductPayment records.

Usage:
    python manage.py backfill_price_audit

This command analyzes all ProductPayment records and creates audit entries
for detected price changes, attributing them to the specified admin user.
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.db.models import Min, Max
from products.models import Product, ProductPayment, ProductAudit
from decimal import Decimal
from datetime import datetime

User = get_user_model()


class Command(BaseCommand):
    help = 'Backfill ProductAudit with historical price changes from ProductPayment records'

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            default='+233597959032',
            help='Phone number of the admin user to attribute changes to (default: +233597959032)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Run without actually creating audit records (preview only)'
        )

    def handle(self, *args, **options):
        phone = options['phone']
        dry_run = options['dry_run']

        self.stdout.write(self.style.WARNING('=' * 70))
        self.stdout.write(self.style.WARNING('BACKFILL PRODUCT AUDIT - Historical Price Changes'))
        self.stdout.write(self.style.WARNING('=' * 70))
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n🔍 DRY RUN MODE - No data will be created\n'))

        # Find admin user by phone
        try:
            admin_user = User.objects.get(phone=phone)
            self.stdout.write(self.style.SUCCESS(
                f'✅ Found admin user: {admin_user.get_full_name() or admin_user.username} '
                f'({admin_user.email})'
            ))
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(
                f'❌ No user found with phone: {phone}'
            ))
            self.stdout.write(self.style.WARNING(
                '\nAvailable admin users:'
            ))
            for user in User.objects.filter(is_staff=True)[:10]:
                self.stdout.write(f'  - {user.get_full_name() or user.username} | {user.phone or "No phone"} | {user.email}')
            return

        self.stdout.write(self.style.WARNING(f'\n📊 Analyzing ProductPayment records...\n'))

        # Debug: Show all products first
        all_products = Product.objects.all()
        self.stdout.write(f'Total products in database: {all_products.count()}')
        
        # Debug: Show products with successful payments
        products_with_successful_payments = Product.objects.filter(
            productpayment__payment_successful=True
        ).distinct()
        self.stdout.write(f'Products with successful payments: {products_with_successful_payments.count()}')

        # Get all products that have payments with amount data
        products_with_payments = Product.objects.filter(
            productpayment__payment_successful=True,
            productpayment__amount__isnull=False  # Use amount field instead of price_at_purchase
        ).distinct()

        total_products = products_with_payments.count()
        self.stdout.write(f'Products with payment amount data: {total_products}')
        
        if total_products == 0:
            self.stdout.write(self.style.ERROR('\n❌ No products found with payment data!'))
            self.stdout.write(self.style.WARNING('\nAll products in database:'))
            for p in all_products[:10]:
                payment_count = ProductPayment.objects.filter(product=p, payment_successful=True).count()
                self.stdout.write(f'  - {p.product_name} | {payment_count} payments')
            return
        
        self.stdout.write('')  # Empty line
        products_with_changes = 0
        total_audit_entries = 0
        products_processed = []

        for idx, product in enumerate(products_with_payments, 1):
            self.stdout.write(f'\n[{idx}/{total_products}] Analyzing: {product.product_name}')

            # Get all payments for this product, ordered by purchase date
            payments = ProductPayment.objects.filter(
                product=product,
                payment_successful=True,
                amount__isnull=False,
                quantity__gt=0  # Must have valid quantity
            ).order_by('payed_at')

            if not payments.exists():
                self.stdout.write(self.style.WARNING('  ⚠️  No payment records found'))
                continue

            # Show total payments being analyzed
            self.stdout.write(f'  📦 Found {payments.count()} payment records to analyze')

            # Calculate unit price for each payment and group by price
            price_timeline = {}
            for payment in payments:
                # Calculate unit price = total amount / quantity
                unit_price = payment.amount / payment.quantity
                # Round to 2 decimal places to avoid floating point issues
                unit_price = round(unit_price, 2)
                
                if unit_price not in price_timeline:
                    price_timeline[unit_price] = {
                        'first_date': payment.payed_at,
                        'last_date': payment.payed_at,
                        'count': 0,
                        'payments': []
                    }
                price_timeline[unit_price]['last_date'] = payment.payed_at
                price_timeline[unit_price]['count'] += 1
                price_timeline[unit_price]['payments'].append(payment)

            # Sort prices by first occurrence (chronological order)
            sorted_prices = sorted(
                price_timeline.items(),
                key=lambda x: x[1]['first_date']
            )

            if len(sorted_prices) == 1:
                # Only one price point - create initial audit
                first_price = sorted_prices[0][0]
                first_date = sorted_prices[0][1]['first_date']
                
                self.stdout.write(self.style.WARNING(
                    f'  ℹ️  Single price point: GH₵ {first_price} '
                    f'({sorted_prices[0][1]["count"]} sales from {first_date.strftime("%Y-%m-%d")})'
                ))
                
                audit_exists = ProductAudit.objects.filter(
                    product=product,
                    action='create'
                ).exists()

                if not audit_exists:
                    if not dry_run:
                        ProductAudit.objects.create(
                            product=product,
                            action='create',
                            changed_by=admin_user,
                            changed_at=first_date,
                            new_values={
                                'price': str(first_price),
                                'product_name': product.product_name
                            },
                            old_values={},
                            changed_fields=['price', 'product_name'],
                            notes=f'Historical data backfill - Product first sold at GH₵ {first_price} on {first_date.strftime("%B %d, %Y")}'
                        )
                        total_audit_entries += 1
                        self.stdout.write(self.style.SUCCESS(
                            f'  ✅ Created initial audit entry for GH₵ {first_price}'
                        ))
                    else:
                        self.stdout.write(self.style.WARNING(
                            f'  🔍 Would create initial audit entry for GH₵ {first_price}'
                        ))
                        total_audit_entries += 1
                else:
                    self.stdout.write(self.style.WARNING('  ⏭️  Initial audit already exists'))
                
                continue

            # Product has multiple price points - PRICE CHANGES DETECTED!
            products_with_changes += 1
            self.stdout.write(self.style.SUCCESS(
                f'  💰 Found {len(sorted_prices)} different prices (PRICE CHANGES!):'
            ))

            price_changes_created = 0
            for i, (price, data) in enumerate(sorted_prices):
                # Show price period with date range
                date_range = f'{data["first_date"].strftime("%b %d, %Y")} → {data["last_date"].strftime("%b %d, %Y")}'
                self.stdout.write(
                    f'     {i+1}. GH₵ {price} | {date_range} | {data["count"]} sales'
                )

                if i == 0:
                    # First price - create as product creation
                    audit_exists = ProductAudit.objects.filter(
                        product=product,
                        action='create',
                        new_values__price=str(price)
                    ).exists()

                    if not audit_exists:
                        if not dry_run:
                            ProductAudit.objects.create(
                                product=product,
                                action='create',
                                changed_by=admin_user,
                                changed_at=data['first_date'],
                                new_values={
                                    'price': str(price),
                                    'product_name': product.product_name
                                },
                                old_values={},
                                changed_fields=['price', 'product_name'],
                                notes=(
                                    f'Historical data backfill - Initial price GH₵ {price}. '
                                    f'First sold on {data["first_date"].strftime("%B %d, %Y")}. '
                                    f'{data["count"]} sales at this price.'
                                )
                            )
                            total_audit_entries += 1
                            price_changes_created += 1
                        else:
                            total_audit_entries += 1
                            price_changes_created += 1
                else:
                    # Subsequent prices - create as PRICE CHANGES
                    old_price = sorted_prices[i-1][0]
                    old_price_end = sorted_prices[i-1][1]['last_date']
                    
                    audit_exists = ProductAudit.objects.filter(
                        product=product,
                        action='price_change',
                        old_values__price=str(old_price),
                        new_values__price=str(price)
                    ).exists()

                    if not audit_exists:
                        price_diff = price - old_price
                        percent_change = (price_diff / old_price * 100) if old_price > 0 else 0

                        if not dry_run:
                            ProductAudit.objects.create(
                                product=product,
                                action='price_change',
                                changed_by=admin_user,
                                changed_at=data['first_date'],
                                old_values={'price': str(old_price)},
                                new_values={'price': str(price)},
                                changed_fields=['price'],
                                notes=(
                                    f'Historical data backfill - PRICE CHANGE detected from payment records.\n'
                                    f'Old price: GH₵ {old_price} (last sale: {old_price_end.strftime("%B %d, %Y")})\n'
                                    f'New price: GH₵ {price} (first sale: {data["first_date"].strftime("%B %d, %Y")})\n'
                                    f'Change: GH₵ {price_diff:+.2f} ({percent_change:+.1f}%)\n'
                                    f'Sales at new price: {data["count"]}'
                                )
                            )
                            total_audit_entries += 1
                            price_changes_created += 1
                            
                            # Show the change clearly
                            arrow = '↑' if price_diff > 0 else '↓'
                            self.stdout.write(self.style.SUCCESS(
                                f'        {arrow} PRICE CHANGE: GH₵ {old_price} → GH₵ {price} '
                                f'({price_diff:+.2f}, {percent_change:+.1f}%)'
                            ))
                        else:
                            total_audit_entries += 1
                            price_changes_created += 1
                            arrow = '↑' if price_diff > 0 else '↓'
                            self.stdout.write(self.style.WARNING(
                                f'        {arrow} Would create: GH₵ {old_price} → GH₵ {price} '
                                f'({price_diff:+.2f}, {percent_change:+.1f}%)'
                            ))

            if price_changes_created > 0:
                self.stdout.write(self.style.SUCCESS(
                    f'  ✅ {"Would create" if dry_run else "Created"} {price_changes_created} audit entries'
                ))
                products_processed.append({
                    'name': product.product_name,
                    'price_points': len(sorted_prices),
                    'audits': price_changes_created
                })

        # Summary
        self.stdout.write('\n' + '=' * 70)
        self.stdout.write(self.style.SUCCESS('📋 BACKFILL SUMMARY'))
        self.stdout.write('=' * 70)
        self.stdout.write(f'Total Products Analyzed: {total_products}')
        self.stdout.write(f'Products with Price Changes: {products_with_changes}')
        self.stdout.write(f'Total Audit Entries {"to be created" if dry_run else "Created"}: {total_audit_entries}')
        self.stdout.write(f'Attributed to: {admin_user.get_full_name() or admin_user.username}')

        if products_processed:
            self.stdout.write('\n📦 Products with Price Changes:')
            for product in products_processed:
                self.stdout.write(
                    f'  • {product["name"]}: {product["price_points"]} prices, '
                    f'{product["audits"]} audit entries'
                )

        if dry_run:
            self.stdout.write(self.style.WARNING(
                '\n⚠️  DRY RUN COMPLETE - No data was actually created.'
            ))
            self.stdout.write(self.style.WARNING(
                'Run without --dry-run to create the audit records.'
            ))
        else:
            self.stdout.write(self.style.SUCCESS(
                '\n✅ BACKFILL COMPLETE - Historical audit data has been created!'
            ))

        self.stdout.write('=' * 70 + '\n')
