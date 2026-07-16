"""
Management command to deactivate students who have completed their program.

This command identifies students who have graduated (based on their graduation_year)
and sets their is_active status to False. This ensures that graduated students
are filtered out from active queries and cannot access student-only features.

Usage:
    python manage.py deactivate_graduated_students
    python manage.py deactivate_graduated_students --dry-run  # Preview without changes
    python manage.py deactivate_graduated_students --force    # Skip confirmation

This command can be scheduled to run automatically:
- At the beginning of each academic year (January)
- At the end of each academic year (December)

To schedule with cron:
    # Run at midnight on January 1st and December 1st
    0 0 1 1,12 * cd /path/to/project && python manage.py deactivate_graduated_students --force
"""

from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone
from accounts.models import CustomUser
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Deactivate students who have completed their program (graduated)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Skip confirmation prompt',
        )
        parser.add_argument(
            '--include-staff',
            action='store_true',
            help='Also deactivate staff members who have graduated (default: skip staff)',
        )

    def get_graduated_students(self, include_staff=False):
        """
        Get all students who have graduated but are still marked as active.
        
        A student is considered graduated if their graduation_year < effective_year,
        where effective_year accounts for the academic year transition in December.
        """
        now = timezone.now()
        current_year = now.year
        current_month = now.month
        
        # After November 30th, use next year as effective year
        adjustment = 1 if (current_month == 12 or (current_month == 11 and now.day > 30)) else 0
        effective_year = current_year + adjustment
        
        # Find users who have graduated but are still active
        queryset = CustomUser.objects.filter(
            graduation_year__lt=effective_year,
            is_active=True,
        )
        
        # Optionally exclude staff members
        if not include_staff:
            queryset = queryset.filter(is_staff=False)
        
        return queryset, effective_year

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        include_staff = options['include_staff']
        
        self.stdout.write(self.style.MIGRATE_HEADING('Deactivating Graduated Students'))
        self.stdout.write('=' * 60)
        
        # Get graduated students
        graduated_students, effective_year = self.get_graduated_students(include_staff)
        count = graduated_students.count()
        
        self.stdout.write(f'\nCurrent effective year: {effective_year}')
        self.stdout.write(f'Students to deactivate: {count}')
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS('\nNo graduated students found that need to be deactivated.'))
            return
        
        # Show details of students to be deactivated
        self.stdout.write(self.style.WARNING(f'\nThe following {count} students will be deactivated:\n'))
        
        for i, student in enumerate(graduated_students[:20], 1):
            self.stdout.write(
                f'  {i}. {student.first_name} {student.last_name} '
                f'(Grad Year: {student.graduation_year}, Phone: {student.phone})'
            )
        
        if count > 20:
            self.stdout.write(f'  ... and {count - 20} more')
        
        if dry_run:
            self.stdout.write(self.style.WARNING('\n[DRY RUN] No changes were made.'))
            return
        
        # Confirm action
        if not force:
            self.stdout.write('')
            confirm = input(f'Are you sure you want to deactivate {count} students? [y/N]: ')
            if confirm.lower() != 'y':
                self.stdout.write(self.style.ERROR('Operation cancelled.'))
                return
        
        # Perform deactivation
        try:
            updated_count = graduated_students.update(is_active=False)
            
            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS(
                f'✓ Successfully deactivated {updated_count} graduated students!'
            ))
            
            # Log the action
            logger.info(
                f'Deactivated {updated_count} graduated students. '
                f'Effective year: {effective_year}, Include staff: {include_staff}'
            )
            
            # Summary
            self.stdout.write('\n' + '=' * 60)
            self.stdout.write('SUMMARY')
            self.stdout.write('=' * 60)
            self.stdout.write(f'  Students deactivated: {updated_count}')
            self.stdout.write(f'  Effective year used: {effective_year}')
            self.stdout.write(f'  Staff included: {"Yes" if include_staff else "No"}')
            self.stdout.write(f'  Timestamp: {timezone.now().strftime("%Y-%m-%d %H:%M:%S")}')
            
        except Exception as e:
            logger.error(f'Error deactivating graduated students: {e}')
            raise CommandError(f'Failed to deactivate students: {e}')
