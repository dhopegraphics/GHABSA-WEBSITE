from django.core.management.base import BaseCommand
from admissions.models import AdmissionCriteria, AdmissionGuideline, FAQ, ImportantDate


class Command(BaseCommand):
    help = 'Clear all existing admission data (criteria, guidelines, FAQs, important dates)'

    def handle(self, *args, **kwargs):
        self.stdout.write('Clearing existing admission data...')
        
        # Delete all existing data
        criteria_count = AdmissionCriteria.objects.all().count()
        AdmissionCriteria.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {criteria_count} admission criteria'))
        
        guidelines_count = AdmissionGuideline.objects.all().count()
        AdmissionGuideline.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {guidelines_count} admission guidelines'))
        
        faqs_count = FAQ.objects.all().count()
        FAQ.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {faqs_count} FAQs'))
        
        dates_count = ImportantDate.objects.all().count()
        ImportantDate.objects.all().delete()
        self.stdout.write(self.style.SUCCESS(f'✓ Deleted {dates_count} important dates'))
        
        self.stdout.write(self.style.SUCCESS('\n✅ Successfully cleared all admission data!'))
        self.stdout.write(self.style.SUCCESS('\nYou can now run: python manage.py populate_admission_data'))
