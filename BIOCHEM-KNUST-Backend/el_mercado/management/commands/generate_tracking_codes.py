"""
Management command to generate tracking codes for existing seller applications.
"""
from django.core.management.base import BaseCommand
from el_mercado.models import SellerApplication


class Command(BaseCommand):
    help = 'Generate tracking codes for seller applications that don\'t have one'

    def handle(self, *args, **options):
        applications = SellerApplication.objects.filter(tracking_code='')
        count = applications.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('All applications already have tracking codes.'))
            return
        
        self.stdout.write(f'Found {count} applications without tracking codes.')
        
        for app in applications:
            app.tracking_code = app.generate_tracking_code()
            app.save(update_fields=['tracking_code'])
            self.stdout.write(f'  Generated {app.tracking_code} for {app.applicant_name}')
        
        self.stdout.write(self.style.SUCCESS(f'Successfully generated {count} tracking codes.'))
