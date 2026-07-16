"""
Management command to resend credentials to recently approved sellers.
This is useful if the automatic email failed during the approval process.

Usage:
    python manage.py resend_seller_credentials              # Dry run (preview)
    python manage.py resend_seller_credentials --execute    # Actually send emails
    python manage.py resend_seller_credentials --days=7     # Check last 7 days
    python manage.py resend_seller_credentials --seller-id=<uuid>  # Specific seller
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from datetime import timedelta
from el_mercado.models import Seller


class Command(BaseCommand):
    help = 'Resend credentials to recently approved sellers who may not have received their email'

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually send emails (without this flag, it just shows what would be done)',
        )
        parser.add_argument(
            '--days',
            type=int,
            default=1,
            help='Check sellers approved in the last N days (default: 1)',
        )
        parser.add_argument(
            '--seller-id',
            type=str,
            help='Resend credentials for a specific seller by UUID',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force resend even if seller has recent login activity',
        )

    def handle(self, *args, **options):
        execute = options['execute']
        days = options['days']
        seller_id = options.get('seller_id')
        force = options['force']

        # Get sellers to process
        if seller_id:
            try:
                sellers = Seller.objects.filter(id=seller_id, status='ACTIVE')
                if not sellers.exists():
                    raise CommandError(f"Active seller with ID {seller_id} not found")
            except Exception as e:
                raise CommandError(f"Invalid seller ID: {e}")
        else:
            # Get recently approved sellers
            cutoff_date = timezone.now() - timedelta(days=days)
            sellers = Seller.objects.filter(
                status='ACTIVE',
                created_at__gte=cutoff_date
            )

        seller_count = sellers.count()
        
        if seller_count == 0:
            self.stdout.write(self.style.SUCCESS(
                f"No sellers found approved in the last {days} day(s)."
            ))
            return

        self.stdout.write(f"\nFound {seller_count} seller(s) approved in the last {days} day(s):\n")
        self.stdout.write("-" * 70)

        credentials_sent = []

        for seller in sellers:
            # Check if seller needs credentials resent
            should_resend = force or not seller.last_login or seller.password == ''
            
            self.stdout.write(f"\n  Seller: {seller.display_name}")
            self.stdout.write(f"  Email: {seller.email}")
            self.stdout.write(f"  Phone: {seller.phone}")
            self.stdout.write(f"  Created: {seller.created_at}")
            self.stdout.write(f"  Last Login: {seller.last_login or 'Never'}")
            self.stdout.write(f"  Has Password: {'Yes' if seller.password else 'No'}")
            self.stdout.write(f"  Should Resend: {'Yes' if should_resend else 'No (use --force to override)'}")

            if execute and should_resend:
                # Generate new temporary password
                temp_password = seller.generate_temporary_password()
                seller.save()
                
                # Send email using the method from SellerApplication
                from el_mercado.models import SellerApplication
                app = SellerApplication()  # Create temporary instance just for the email method
                email_sent = app._send_credentials_email(seller, temp_password)
                
                if email_sent:
                    self.stdout.write(self.style.SUCCESS(f"  ✓ Credentials sent to {seller.email}"))
                    credentials_sent.append({
                        'seller': seller,
                        'password': temp_password,
                        'email_sent': True
                    })
                else:
                    self.stdout.write(self.style.WARNING(f"  ⚠ Failed to send email to {seller.email}"))
                    credentials_sent.append({
                        'seller': seller,
                        'password': temp_password,
                        'email_sent': False
                    })
            elif execute and not should_resend:
                self.stdout.write(self.style.WARNING(f"  → Skipped (use --force to resend anyway)"))
            else:
                self.stdout.write(self.style.WARNING(f"  [DRY RUN] Would resend credentials"))

        self.stdout.write("\n" + "-" * 70)
        
        if execute:
            success_count = sum(1 for c in credentials_sent if c['email_sent'])
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Sent credentials to {success_count}/{len(credentials_sent)} seller(s)"
            ))
            
            # Print summary of generated credentials
            if credentials_sent:
                self.stdout.write("\n" + "=" * 70)
                self.stdout.write("CREDENTIALS SUMMARY")
                self.stdout.write("=" * 70 + "\n")
                
                for cred in credentials_sent:
                    status = "✓ Email sent" if cred['email_sent'] else "⚠ Email failed"
                    self.stdout.write(f"Seller: {cred['seller'].display_name}")
                    self.stdout.write(f"Email: {cred['seller'].email}")
                    self.stdout.write(f"Password: {cred['password']}")
                    self.stdout.write(f"Status: {status}")
                    self.stdout.write("-" * 40)
        else:
            resend_count = sum(1 for seller in sellers if force or not seller.last_login or seller.password == '')
            self.stdout.write(self.style.WARNING(
                f"\n[DRY RUN] Would resend credentials to {resend_count} seller(s)"
            ))
            self.stdout.write(
                "Run with --execute flag to actually send credentials"
            )