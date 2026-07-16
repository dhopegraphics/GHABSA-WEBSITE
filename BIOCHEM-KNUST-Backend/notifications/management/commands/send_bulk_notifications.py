"""
Management command to send bulk notifications
Usage:
    python manage.py send_bulk_notifications --type exam --exam-id <uuid>
    python manage.py send_bulk_notifications --type class --class-id <uuid>
    python manage.py send_bulk_notifications --type custom --title "Title" --body "Body" --year 2
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from notifications.services import BulkNotificationService
from accounts.models import CustomUser
from timetable_system.models import ExaminationSchedule, ClassSchedule


class Command(BaseCommand):
    help = 'Send bulk personalized notifications to users'

    def add_arguments(self, parser):
        parser.add_argument(
            '--type',
            type=str,
            choices=['exam', 'class', 'custom'],
            required=True,
            help='Type of notification to send'
        )
        
        parser.add_argument(
            '--exam-id',
            type=str,
            help='UUID of exam schedule (required for exam type)'
        )
        
        parser.add_argument(
            '--class-id',
            type=str,
            help='UUID of class schedule (required for class type)'
        )
        
        parser.add_argument(
            '--title',
            type=str,
            help='Notification title (required for custom type)'
        )
        
        parser.add_argument(
            '--body',
            type=str,
            help='Notification body (required for custom type)'
        )
        
        parser.add_argument(
            '--priority',
            type=str,
            choices=['low', 'normal', 'high'],
            default='normal',
            help='Notification priority (for custom type)'
        )
        
        parser.add_argument(
            '--year',
            type=int,
            choices=[1, 2, 3, 4],
            help='Filter users by year (1, 2, 3, or 4)'
        )
        
        parser.add_argument(
            '--all-users',
            action='store_true',
            help='Send to all active users'
        )
        
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be sent without actually sending'
        )

    def handle(self, *args, **options):
        notification_type = options['type']
        dry_run = options['dry_run']
        
        # Get target users
        users = CustomUser.objects.filter(is_active=True)
        
        if options['year']:
            # Filter users by year - need to calculate graduation_year
            from datetime import datetime
            current_year = datetime.now().year
            # year = 4 - diff, so diff = 4 - year, so graduation_year = current_year + (4 - year)
            target_graduation_year = current_year + (4 - options['year'])
            users = users.filter(graduation_year=target_graduation_year)
            self.stdout.write(f"Filtering users by year: {options['year']}")
        elif not options['all_users']:
            self.stdout.write(self.style.WARNING(
                'No user filter specified. Use --all-users to send to all active users or --year to filter by year.'
            ))
            return
        
        user_count = users.count()
        
        if user_count == 0:
            self.stdout.write(self.style.ERROR('No users found matching criteria'))
            return
        
        self.stdout.write(f"Target: {user_count} users")
        
        if dry_run:
            self.stdout.write(self.style.WARNING('DRY RUN - No notifications will be sent'))
            self.stdout.write(f"Would send to: {', '.join([u.username for u in users[:10]])}...")
            return
        
        # Handle different notification types
        if notification_type == 'exam':
            if not options['exam_id']:
                self.stdout.write(self.style.ERROR('--exam-id is required for exam notifications'))
                return
            
            try:
                exam = ExaminationSchedule.objects.get(id=options['exam_id'])
            except ExaminationSchedule.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Exam schedule not found: {options['exam_id']}"))
                return
            
            # Filter users by index number range
            users = users.filter(
                index_number__gte=exam.index_number_start,
                index_number__lte=exam.index_number_end
            )
            
            self.stdout.write(f"Sending exam notifications for: {exam.course.course_code}")
            self.stdout.write(f"Filtered to {users.count()} users by index range")
            
            results = BulkNotificationService.send_exam_notifications_to_users(users, exam)
            
        elif notification_type == 'class':
            if not options['class_id']:
                self.stdout.write(self.style.ERROR('--class-id is required for class notifications'))
                return
            
            try:
                class_schedule = ClassSchedule.objects.get(id=options['class_id'])
            except ClassSchedule.DoesNotExist:
                self.stdout.write(self.style.ERROR(f"Class schedule not found: {options['class_id']}"))
                return
            
            # Filter users by program and year
            users = users.filter(
                program=class_schedule.program,
                year=class_schedule.year,
            )
            
            self.stdout.write(f"Sending class notifications for: {class_schedule.course.course_code}")
            self.stdout.write(f"Filtered to {users.count()} users by program/year")
            
            results = BulkNotificationService.send_class_notifications_to_users(users, class_schedule)
            
        elif notification_type == 'custom':
            if not options['title'] or not options['body']:
                self.stdout.write(self.style.ERROR('--title and --body are required for custom notifications'))
                return
            
            self.stdout.write(f"Sending custom notification: {options['title']}")
            
            results = BulkNotificationService.send_custom_bulk_notification(
                users=users,
                title=options['title'],
                body=options['body'],
                priority=options['priority']
            )
        
        # Display results
        self.stdout.write(self.style.SUCCESS('\n=== Results ==='))
        self.stdout.write(f"Total: {results['total']}")
        self.stdout.write(self.style.SUCCESS(f"✅ Success: {results['success']}"))
        self.stdout.write(self.style.ERROR(f"❌ Failed: {results['failed']}"))
        
        if results.get('skipped'):
            self.stdout.write(self.style.WARNING(f"⏭️  Skipped: {results['skipped']}"))
        
        if results['errors']:
            self.stdout.write(self.style.ERROR('\nErrors:'))
            for error in results['errors'][:10]:  # Show first 10 errors
                self.stdout.write(f"  - {error['user']}: {error['error']}")
            
            if len(results['errors']) > 10:
                self.stdout.write(f"  ... and {len(results['errors']) - 10} more errors")
