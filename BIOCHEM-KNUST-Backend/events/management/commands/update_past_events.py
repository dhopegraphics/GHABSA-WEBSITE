from django.core.management.base import BaseCommand
from django.utils import timezone
from events.models import Event


class Command(BaseCommand):
    help = "Automatically set end_date for past events that don't have one"

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be updated without making changes',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        now = timezone.now()
        
        # Find events that are past but don't have end_date set
        past_events = Event.objects.filter(
            event_date__lt=now,
            event_end_date__isnull=True
        )
        
        count = past_events.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('No past events need updating!'))
            return
        
        if dry_run:
            self.stdout.write(self.style.WARNING(f'DRY RUN: Would update {count} past event(s):'))
            for event in past_events:
                self.stdout.write(f'  - {event.event_name} (Date: {event.event_date})')
        else:
            # Update: Set end_date to the event_date (end of that day)
            updated = 0
            for event in past_events:
                event.event_end_date = event.event_date.replace(
                    hour=23, minute=59, second=59, microsecond=999999
                )
                event.save()
                updated += 1
                self.stdout.write(f'  ✓ Updated: {event.event_name}')
            
            self.stdout.write(self.style.SUCCESS(f'\nSuccessfully updated {updated} past event(s)!'))
