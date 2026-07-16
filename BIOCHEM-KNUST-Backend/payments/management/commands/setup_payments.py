"""
Setup Payment System
Run this script to initialize payment gateways and currencies
"""
from django.core.management.base import BaseCommand
from payments.models import PaymentGateway, Currency
from decimal import Decimal


class Command(BaseCommand):
    help = 'Initialize payment gateways and currencies'
    
    def handle(self, *args, **kwargs):
        self.stdout.write('Initializing Payment System...\n')
        
        # Create currencies
        self.stdout.write('Creating currencies...')
        
        currencies_data = [
            {
                'code': 'GHS',
                'name': 'Ghana Cedis',
                'symbol': 'GH₵',
                'exchange_rate': Decimal('1.0'),
                'is_base_currency': True,
                'is_active': True
            },
            {
                'code': 'USD',
                'name': 'US Dollar',
                'symbol': '$',
                'exchange_rate': Decimal('0.084'),
                'is_active': True
            },
            {
                'code': 'EUR',
                'name': 'Euro',
                'symbol': '€',
                'exchange_rate': Decimal('0.077'),
                'is_active': True
            },
            {
                'code': 'GBP',
                'name': 'British Pound',
                'symbol': '£',
                'exchange_rate': Decimal('0.066'),
                'is_active': True
            },
        ]
        
        for currency_data in currencies_data:
            currency, created = Currency.objects.get_or_create(
                code=currency_data['code'],
                defaults=currency_data
            )
            if created:
                self.stdout.write(
                    self.style.SUCCESS(f'  ✓ Created currency: {currency.code} - {currency.name}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  ⚠ Currency already exists: {currency.code}')
                )
        
        # Create Paystack gateway
        self.stdout.write('\nCreating payment gateways...')
        
        paystack_data = {
            'name': 'paystack',
            'display_name': 'Paystack',
            'description': 'Paystack Payment Gateway - Ghana & International',
            'is_active': True,
            'status': 'active',
            'supports_refunds': True,
            'supports_recurring': True,
            'supports_webhooks': True,
            'supported_currencies': ['GHS', 'USD', 'EUR', 'GBP', 'NGN', 'ZAR'],
            'supported_methods': ['card', 'bank_transfer', 'mobile_money', 'ussd', 'qr'],
            'fixed_fee': Decimal('0.00'),
            'percentage_fee': Decimal('1.95'),
            'priority': 1,
            'config': {
                'test_mode': True,
                'channels': ['card', 'bank', 'mobile_money'],
            }
        }
        
        paystack, created = PaymentGateway.objects.get_or_create(
            name='paystack',
            defaults=paystack_data
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ Created gateway: {paystack.display_name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'  ⚠ Gateway already exists: {paystack.display_name}')
            )
        
        # Create Manual gateway (for cash/bank transfer)
        manual_data = {
            'name': 'manual',
            'display_name': 'Manual Payment',
            'description': 'Manual payment verification for cash/bank transfer',
            'is_active': True,
            'status': 'active',
            'supports_refunds': True,
            'supports_recurring': False,
            'supports_webhooks': False,
            'supported_currencies': ['GHS', 'USD', 'EUR', 'GBP'],
            'supported_methods': ['cash', 'bank_transfer', 'cheque'],
            'fixed_fee': Decimal('0.00'),
            'percentage_fee': Decimal('0.00'),
            'priority': 99,
            'config': {}
        }
        
        manual, created = PaymentGateway.objects.get_or_create(
            name='manual',
            defaults=manual_data
        )
        
        if created:
            self.stdout.write(
                self.style.SUCCESS(f'  ✓ Created gateway: {manual.display_name}')
            )
        else:
            self.stdout.write(
                self.style.WARNING(f'  ⚠ Gateway already exists: {manual.display_name}')
            )
        
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\n✓ Payment system initialized successfully!\n'))
        self.stdout.write('='*60 + '\n')
        
        self.stdout.write('Next steps:')
        self.stdout.write('1. Update Paystack credentials in admin or .env file')
        self.stdout.write('2. Configure webhook URL in Paystack dashboard')
        self.stdout.write('3. Test payment flow with test keys')
        self.stdout.write('4. Switch to live keys for production\n')
