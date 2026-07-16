"""
Management command to calculate processing fees for existing payout requests.
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from el_mercado.models import PayoutRequest, MarketplaceSettings
from decimal import Decimal


class Command(BaseCommand):
    help = 'Calculate and set processing fees for existing payout requests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']

        if dry_run:
            self.stdout.write(self.style.WARNING('🔍 DRY RUN MODE - No changes will be made\n'))

        # Get all payout requests that don't have processing fee calculated
        payouts = PayoutRequest.objects.filter(processing_fee=Decimal('0.00'))

        if not payouts.exists():
            self.stdout.write(self.style.SUCCESS('✅ All payout requests already have processing fees calculated'))
            return

        self.stdout.write(f'Processing {payouts.count()} payout request(s)...\n')

        # Get fee percentage from settings
        settings = MarketplaceSettings.get_settings()
        fee_percentage = settings.payout_processing_fee_percentage / Decimal('100')
        self.stdout.write(f'Using fee percentage: {settings.payout_processing_fee_percentage}%\n')

        updated_count = 0
        total_fees = Decimal('0.00')

        for payout in payouts:
            # Calculate processing fee from settings
            processing_fee = (payout.amount * fee_percentage).quantize(Decimal('0.01'))
            net_amount = payout.amount - processing_fee

            self.stdout.write(f'📝 Payout {payout.reference}:')
            self.stdout.write(f'   Amount: GH₵{payout.amount}')
            self.stdout.write(f'   Processing Fee ({settings.payout_processing_fee_percentage}%): GH₵{processing_fee}')
            self.stdout.write(f'   Net Amount: GH₵{net_amount}')

            if dry_run:
                self.stdout.write(self.style.WARNING('   Would update\n'))
            else:
                with transaction.atomic():
                    payout.processing_fee = processing_fee
                    payout.net_amount = net_amount
                    payout.save(update_fields=['processing_fee', 'net_amount'])
                self.stdout.write(self.style.SUCCESS('   ✅ Updated\n'))
                updated_count += 1
                total_fees += processing_fee

        # Summary
        self.stdout.write('\n' + '='*60)
        if dry_run:
            self.stdout.write(self.style.WARNING(f'Would update {payouts.count()} payout request(s)'))
        else:
            self.stdout.write(self.style.SUCCESS(f'✅ Updated {updated_count} payout request(s)'))
            self.stdout.write(self.style.SUCCESS(f'✅ Total processing fees: GH₵{total_fees}'))
