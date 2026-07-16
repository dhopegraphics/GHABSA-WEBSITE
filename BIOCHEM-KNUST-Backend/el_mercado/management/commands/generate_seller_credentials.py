"""
Management command to generate credentials for existing sellers.
This is for sellers who were approved before the authentication system was implemented.

Usage:
    python manage.py generate_seller_credentials              # Dry run (preview)
    python manage.py generate_seller_credentials --execute    # Actually generate and send
    python manage.py generate_seller_credentials --seller-id=<uuid>  # Single seller
    python manage.py generate_seller_credentials --no-email   # Don't send emails
"""

from django.core.management.base import BaseCommand, CommandError
from django.core.mail import send_mail
from django.conf import settings
from el_mercado.models import Seller


class Command(BaseCommand):
    help = 'Generate login credentials for existing sellers who do not have passwords'

    def add_arguments(self, parser):
        parser.add_argument(
            '--execute',
            action='store_true',
            help='Actually generate credentials (without this flag, it just shows what would be done)',
        )
        parser.add_argument(
            '--seller-id',
            type=str,
            help='Generate credentials for a specific seller by UUID',
        )
        parser.add_argument(
            '--no-email',
            action='store_true',
            help='Do not send email notifications',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force regenerate even if seller already has credentials',
        )

    def handle(self, *args, **options):
        execute = options['execute']
        seller_id = options.get('seller_id')
        no_email = options['no_email']
        force = options['force']

        # Get sellers to process
        if seller_id:
            try:
                sellers = Seller.objects.filter(id=seller_id)
                if not sellers.exists():
                    raise CommandError(f"Seller with ID {seller_id} not found")
            except Exception as e:
                raise CommandError(f"Invalid seller ID: {e}")
        else:
            # Get sellers without passwords (empty password field)
            if force:
                sellers = Seller.objects.filter(status='ACTIVE')
            else:
                sellers = Seller.objects.filter(
                    status='ACTIVE',
                    password=''
                )

        seller_count = sellers.count()
        
        if seller_count == 0:
            self.stdout.write(self.style.SUCCESS("No sellers need credentials generated."))
            return

        self.stdout.write(f"\nFound {seller_count} seller(s) needing credentials:\n")
        self.stdout.write("-" * 70)

        credentials_generated = []

        for seller in sellers:
            self.stdout.write(f"\n  Seller: {seller.display_name}")
            self.stdout.write(f"  Email: {seller.email}")
            self.stdout.write(f"  Phone: {seller.phone}")
            self.stdout.write(f"  Type: {seller.get_seller_type_display()}")
            self.stdout.write(f"  Has Password: {'Yes' if seller.password else 'No'}")

            if execute:
                # Generate temporary password
                temp_password = seller.generate_temporary_password()
                seller.save()
                
                credentials_generated.append({
                    'seller': seller,
                    'password': temp_password
                })
                
                self.stdout.write(self.style.SUCCESS(f"  ✓ Generated password: {temp_password}"))
                
                # Send email if enabled
                if not no_email and seller.email:
                    success = self._send_credentials_email(seller, temp_password)
                    if success:
                        self.stdout.write(self.style.SUCCESS(f"  ✓ Email sent to {seller.email}"))
                    else:
                        self.stdout.write(self.style.WARNING(f"  ⚠ Failed to send email"))
            else:
                self.stdout.write(self.style.WARNING(f"  [DRY RUN] Would generate credentials"))

        self.stdout.write("\n" + "-" * 70)
        
        if execute:
            self.stdout.write(self.style.SUCCESS(
                f"\n✓ Generated credentials for {len(credentials_generated)} seller(s)"
            ))
            
            # Print summary of generated credentials (for manual sharing if email fails)
            if credentials_generated:
                self.stdout.write("\n" + "=" * 70)
                self.stdout.write("GENERATED CREDENTIALS SUMMARY")
                self.stdout.write("(Save this if you need to share credentials manually)")
                self.stdout.write("=" * 70 + "\n")
                
                for cred in credentials_generated:
                    self.stdout.write(f"Seller: {cred['seller'].display_name}")
                    self.stdout.write(f"Email: {cred['seller'].email}")
                    self.stdout.write(f"Phone: {cred['seller'].phone}")
                    self.stdout.write(f"Password: {cred['password']}")
                    self.stdout.write("-" * 40)
        else:
            self.stdout.write(self.style.WARNING(
                f"\n[DRY RUN] Would generate credentials for {seller_count} seller(s)"
            ))
            self.stdout.write(
                "Run with --execute flag to actually generate credentials"
            )

    def _send_credentials_email(self, seller, temp_password):
        """Send credentials email to seller with HTML template"""
        from django.core.mail import EmailMultiAlternatives
        from django.template.loader import render_to_string
        from django.utils.html import strip_tags
        from datetime import datetime
        
        login_url = getattr(
            settings, 
            'SELLER_PORTAL_LOGIN_URL', 
            f"{getattr(settings, 'BACKEND_URL', 'https://api.biochemknust.com')}/api/el-mercado/seller/login/"
        )

        from BioChemSystem.config.brand import get_brand_context
        # Context for the template
        context = {
            **get_brand_context(),
            'seller_name': seller.display_name,
            'seller_email': seller.email,
            'seller_phone': str(seller.phone),
            'temp_password': temp_password,
            'login_url': login_url,
            'year': datetime.now().year,
        }
        
        # Render HTML template
        try:
            html_content = render_to_string('el_mercado/emails/seller_credentials.html', context)
            text_content = strip_tags(html_content)  # Fallback plain text
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"  Template error, using plain text: {e}"))
            # Fallback to plain text if template fails
            text_content = f"""
Hello {seller.display_name},

Your El Mercado seller dashboard login credentials have been generated.

LOGIN DETAILS:
--------------
Login URL: {login_url}
Email: {seller.email}
Phone: {seller.phone}
Temporary Password: {temp_password}

Please change your password after your first login.

Thank you for being a seller on El Mercado!

Best regards,
The El Mercado Team
            """
            html_content = None
        
        try:
            email = EmailMultiAlternatives(
                subject='🛍️ El Mercado - Your Seller Dashboard is Ready!',
                body=text_content,
                from_email=settings.DEFAULT_FROM_EMAIL,
                to=[seller.email],
            )
            
            if html_content:
                email.attach_alternative(html_content, "text/html")
            
            email.send(fail_silently=False)
            return True
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  Email error: {e}"))
            return False
