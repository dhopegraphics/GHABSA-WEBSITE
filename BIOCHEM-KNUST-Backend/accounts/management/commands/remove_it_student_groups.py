"""
Management command to remove group values from IT students.

IT students should not have groups assigned as they are not divided into groups
like Computer Science students (G1, G2).

Usage:
    python manage.py remove_it_student_groups --dry-run   # Preview changes
    python manage.py remove_it_student_groups             # Apply changes
"""

from django.core.management.base import BaseCommand
from accounts.models import CustomUser


class Command(BaseCommand):
    help = 'Remove group values from IT students (IT students should not have groups)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Preview changes without actually modifying the database',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(self.style.NOTICE('=' * 60))
        self.stdout.write(self.style.NOTICE('IT Student Group Cleanup'))
        self.stdout.write(self.style.NOTICE('=' * 60))
        
        # Find IT students with groups assigned
        it_students_with_groups = CustomUser.objects.filter(
            program='IT',
            group__isnull=False
        ).exclude(group='')
        
        count = it_students_with_groups.count()
        
        if count == 0:
            self.stdout.write(self.style.SUCCESS(
                '\n✅ No IT students with groups found. Nothing to clean up.'
            ))
            return
        
        self.stdout.write(self.style.WARNING(
            f'\n⚠️  Found {count} IT student(s) with groups assigned:'
        ))
        
        # List affected students
        for student in it_students_with_groups[:20]:  # Show first 20
            group_display = dict(CustomUser.GROUP_CHOICES).get(student.group, student.group)
            self.stdout.write(
                f'   - {student.first_name} {student.last_name} ({student.phone}) '
                f'- Currently: {group_display}'
            )
        
        if count > 20:
            self.stdout.write(f'   ... and {count - 20} more')
        
        if dry_run:
            self.stdout.write(self.style.WARNING(
                f'\n🔍 DRY RUN: Would remove groups from {count} IT student(s).'
            ))
            self.stdout.write(self.style.NOTICE(
                'Run without --dry-run to apply changes.'
            ))
        else:
            # Confirm before proceeding
            self.stdout.write(self.style.WARNING(
                f'\n⚠️  This will remove groups from {count} IT student(s).'
            ))
            
            # Perform the update
            updated_count = it_students_with_groups.update(group=None)
            
            self.stdout.write(self.style.SUCCESS(
                f'\n✅ Successfully removed groups from {updated_count} IT student(s).'
            ))
        
        # Summary statistics
        self.stdout.write(self.style.NOTICE('\n' + '=' * 60))
        self.stdout.write(self.style.NOTICE('Summary Statistics:'))
        self.stdout.write(self.style.NOTICE('=' * 60))
        
        total_cs = CustomUser.objects.filter(program='CS').count()
        cs_with_groups = CustomUser.objects.filter(program='CS', group__isnull=False).exclude(group='').count()
        cs_without_groups = total_cs - cs_with_groups
        
        total_it = CustomUser.objects.filter(program='IT').count()
        it_with_groups = CustomUser.objects.filter(program='IT', group__isnull=False).exclude(group='').count()
        
        self.stdout.write(f'\nComputer Science (CS):')
        self.stdout.write(f'   Total: {total_cs}')
        self.stdout.write(f'   With groups: {cs_with_groups}')
        self.stdout.write(f'   Without groups: {cs_without_groups} (need to set)')
        
        self.stdout.write(f'\nInformation Technology (IT):')
        self.stdout.write(f'   Total: {total_it}')
        self.stdout.write(f'   With groups: {it_with_groups} (should be 0)')
        
        if not dry_run and it_with_groups > 0:
            self.stdout.write(self.style.ERROR(
                f'\n❌ Warning: {it_with_groups} IT students still have groups!'
            ))
        elif not dry_run:
            self.stdout.write(self.style.SUCCESS(
                '\n✅ All IT students are correctly without groups.'
            ))
