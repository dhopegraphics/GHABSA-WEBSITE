"""
Management command to manually link unlinked gift/on-behalf purchases to users.
"""
from django.core.management.base import BaseCommand
from django.db.models import Q
from accounts.models import CustomUser
from products.models import ProductPayment


class Command(BaseCommand):
    help = 'Link unlinked gift and on-behalf purchases to existing users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--phone',
            type=str,
            help='Specific phone number to link purchases for (e.g., +233599041200)',
        )
        parser.add_argument(
            '--all',
            action='store_true',
            help='Link all unlinked purchases for all users',
        )

    def handle(self, *args, **options):
        phone = options.get('phone')
        link_all = options.get('all')

        if phone:
            # Link purchases for specific phone number
            self.link_for_phone(phone)
        elif link_all:
            # Link all unlinked purchases
            self.link_all_purchases()
        else:
            self.stdout.write(self.style.ERROR('Please specify --phone <number> or --all'))

    def link_for_phone(self, phone_number):
        """Link purchases for a specific phone number"""
        self.stdout.write(f"Looking for user with phone: {phone_number}")
        
        # Normalize phone
        phone_digits = ''.join(filter(str.isdigit, phone_number))[-9:]
        
        # Find user
        user = CustomUser.objects.filter(phone__icontains=phone_digits).first()
        
        if not user:
            self.stdout.write(self.style.ERROR(f'No user found with phone containing: {phone_digits}'))
            return
        
        self.stdout.write(self.style.SUCCESS(f'Found user: {user.student_id or user.phone} ({user.first_name} {user.last_name})'))
        
        # Find unlinked purchases for this phone
        unlinked = ProductPayment.objects.filter(
            Q(is_gift_purchase=True) | Q(is_purchase_on_behalf=True),
            purchased_for_user__isnull=True,
            purchased_for_phone__icontains=phone_digits
        )
        
        count = unlinked.count()
        self.stdout.write(f'Found {count} unlinked purchase(s) for this phone')
        
        if count == 0:
            return
        
        # Link them
        linked = 0
        for purchase in unlinked:
            if purchase.link_to_recipient(user):
                linked += 1
                purchase_type = "Gift" if purchase.is_gift_purchase else "On-behalf"
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Linked {purchase_type} purchase: {purchase.product.product_name} '
                        f'(Payment ID: {purchase.payment_id})'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Successfully linked {linked}/{count} purchase(s) to user {user.student_id or user.phone}')
        )

    def link_all_purchases(self):
        """Link all unlinked purchases to their respective users"""
        self.stdout.write('Linking all unlinked gift/on-behalf purchases...\n')
        
        # Get all users with phone numbers
        users = CustomUser.objects.filter(phone__isnull=False).exclude(phone='')
        total_linked = 0
        
        for user in users:
            linked = ProductPayment.link_purchases_for_user(user)
            if linked > 0:
                total_linked += linked
                self.stdout.write(
                    self.style.SUCCESS(
                        f'✓ Linked {linked} purchase(s) to {user.student_id or user.phone}'
                    )
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'\n✅ Total: Linked {total_linked} purchase(s) across all users')
        )
