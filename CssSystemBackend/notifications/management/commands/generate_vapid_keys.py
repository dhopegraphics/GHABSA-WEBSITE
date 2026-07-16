"""
Management command to generate VAPID keys for Web Push notifications
Usage: python manage.py generate_vapid_keys
"""
from django.core.management.base import BaseCommand
import base64
from cryptography.hazmat.primitives.asymmetric import ec
from cryptography.hazmat.primitives import serialization


class Command(BaseCommand):
    help = 'Generate VAPID keys for Web Push notifications'

    def handle(self, *args, **options):
        self.stdout.write(self.style.WARNING('\nGenerating VAPID keys for Web Push notifications...\n'))
        
        try:
            # Generate private key
            private_key = ec.generate_private_key(ec.SECP256R1())
            
            # Serialize private key
            private_key_bytes = private_key.private_bytes(
                encoding=serialization.Encoding.PEM,
                format=serialization.PrivateFormat.PKCS8,
                encryption_algorithm=serialization.NoEncryption()
            )
            
            # Get public key
            public_key = private_key.public_key()
            public_key_bytes = public_key.public_bytes(
                encoding=serialization.Encoding.X962,
                format=serialization.PublicFormat.UncompressedPoint
            )
            
            # Encode as URL-safe base64
            vapid_keys = {
                'public_key': base64.urlsafe_b64encode(public_key_bytes).decode('utf-8').rstrip('='),
                'private_key': private_key_bytes.decode('utf-8')
            }
            
            self.stdout.write(self.style.SUCCESS('✅ VAPID keys generated successfully!\n'))
            self.stdout.write(self.style.SUCCESS('Add these to your .env file:\n'))
            self.stdout.write('=' * 80)
            self.stdout.write(f'\nVAPID_PUBLIC_KEY={vapid_keys["public_key"]}')
            self.stdout.write(f'\nVAPID_PRIVATE_KEY={vapid_keys["private_key"]}')
            self.stdout.write('\nVAPID_ADMIN_EMAIL=admin@cssknust.com')
            self.stdout.write('\n' + '=' * 80)
            self.stdout.write('\n')
            
            self.stdout.write(self.style.WARNING('⚠️  IMPORTANT:'))
            self.stdout.write('1. Keep the private key SECRET and secure')
            self.stdout.write('2. Never commit these keys to version control')
            self.stdout.write('3. Update VAPID_ADMIN_EMAIL with your actual contact email')
            self.stdout.write('4. Restart your Django server after updating .env file\n')
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'Error generating VAPID keys: {str(e)}'))
