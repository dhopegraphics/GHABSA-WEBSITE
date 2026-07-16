"""
Management command to generate class schedule notifications
This command should be run daily (e.g., 6:00 AM) to create notifications for today's and tomorrow's classes

Usage:
    python manage.py generate_class_notifications
    python manage.py generate_class_notifications --dry-run
    python manage.py generate_class_notifications --days 2
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta, datetime
from notifications.models import NotificationTrigger, PushNotification
from timetable_system.models import ClassSchedule
from accounts.models import CustomUser
from notifications.services import NotificationScheduler
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate push notifications for upcoming class schedules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=2,
            help='Number of days ahead to check (default: 2)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days_ahead = options['days']
        
        self.stdout.write(self.style.WARNING(
            f"🔍 Generating class schedule notifications for next {days_ahead} day(s)..."
        ))
        
        # Get active triggers for class schedules
        triggers = NotificationTrigger.objects.filter(
            trigger_type='class_schedule',
            is_active=True
        ).select_related('template')
        
        if not triggers.exists():
            self.stdout.write(self.style.ERROR(
                "❌ No active class schedule triggers found. "
                "Please create notification triggers in Django Admin."
            ))
            return
        
        self.stdout.write(f"Found {triggers.count()} active trigger(s)")
        
        created_count = 0
        skipped_count = 0
        now = timezone.now()
        today = now.date()
        current_year = datetime.now().year
        
        # Get current day of week (1=Monday, 7=Sunday)
        current_day = now.isoweekday()
        
        # Get days to check
        days_to_check = []
        for i in range(days_ahead):
            day = current_day + i
            if day > 7:
                day = day - 7
            days_to_check.append(day)
        
        self.stdout.write(f"Checking days: {days_to_check}")
        
        # Get all schedules for these days
        schedules = ClassSchedule.objects.filter(
            day_of_week__in=days_to_check
        ).select_related('course')
        
        total_schedules = schedules.count()
        self.stdout.write(f"Found {total_schedules} class schedule(s)")
        
        for schedule in schedules:
            # Determine the actual date for this schedule
            days_diff = schedule.day_of_week - current_day
            if days_diff < 0:
                days_diff += 7
            schedule_date = today + timedelta(days=days_diff)
            
            # Combine date and time
            schedule_datetime = timezone.make_aware(
                datetime.combine(schedule_date, schedule.start_time)
            )
            
            # Skip if schedule is in the past
            if schedule_datetime <= now:
                skipped_count += 1
                continue
            
            self.stdout.write(
                f"\n📅 Class: {schedule.course.course_code} - "
                f"{schedule_datetime.strftime('%A, %Y-%m-%d %H:%M')}"
            )
            
            # Get users for this schedule based on program, year, and group
            users = CustomUser.objects.filter(
                program=schedule.program,
                is_active=True,
                notification_preferences__class_reminders=True,
                notification_preferences__push_enabled=True,
            )
            
            # Filter by year
            current_year_num = current_year
            valid_users = []
            for user in users:
                if not user.graduation_year:
                    continue
                
                # Calculate user's year (1-4)
                user_year = user.get_year()
                
                if user_year == schedule.year:  # Both are now year values (1-4)
                    if schedule.group in ['all', user.group]:
                        valid_users.append(user)
            
            user_count = len(valid_users)
            self.stdout.write(f"  Target users: {user_count}")
            
            if user_count == 0:
                skipped_count += 1
                self.stdout.write(self.style.WARNING("  ⚠️  No users found, skipping"))
                continue
            
            for trigger in triggers:
                notification_time = trigger.calculate_notification_time(schedule_datetime)
                
                # Only create notifications for future times
                if notification_time <= now:
                    self.stdout.write(
                        f"  ⏭️  Skipping trigger '{trigger.name}' "
                        f"(notification time {notification_time} is in the past)"
                    )
                    continue
                
                # Prepare context for template
                context = {
                    'course_name': schedule.course.course_name,
                    'course_code': schedule.course.course_code,
                    'day': schedule.get_day_of_week_display(),
                    'start_time': schedule.start_time.strftime('%I:%M %p'),
                    'end_time': schedule.end_time.strftime('%I:%M %p'),
                    'room': schedule.room or 'TBA',
                    'program': schedule.get_program_display(),
                    'year': schedule.year,
                    'group': schedule.get_group_display(),
                    'schedule_id': str(schedule.id),
                }
                
                # Render notification from template
                rendered = trigger.template.render(context)
                
                self.stdout.write(
                    f"  📬 Trigger: {trigger.name} "
                    f"(Send at {notification_time.strftime('%Y-%m-%d %H:%M')})"
                )
                self.stdout.write(f"     Title: {rendered['title']}")
                self.stdout.write(f"     Body: {rendered['body'][:60]}...")
                
                if dry_run:
                    self.stdout.write(self.style.NOTICE(
                        f"     🔍 DRY RUN: Would create {user_count} notification(s)"
                    ))
                    created_count += user_count
                    continue
                
                # Create notifications for each user
                for user in valid_users:
                    # Check if notification already exists
                    exists = PushNotification.objects.filter(
                        user=user,
                        trigger_type='class_schedule',
                        trigger_id=str(schedule.id),
                        scheduled_at=notification_time,
                        status='scheduled'
                    ).exists()
                    
                    if exists:
                        continue
                    
                    NotificationScheduler.schedule_notification(
                        user=user,
                        title=rendered['title'],
                        body=rendered['body'],
                        scheduled_at=notification_time,
                        template=trigger.template,
                        trigger_type='class_schedule',
                        trigger_id=str(schedule.id),
                        data=rendered.get('data', {}),
                        sound=rendered.get('sound', 'default'),
                        priority=rendered.get('priority', 'default'),
                        badge=rendered.get('badge', 1),
                        category=rendered.get('category', 'class'),
                    )
                    created_count += 1
                
                self.stdout.write(self.style.SUCCESS(
                    f"     ✅ Created {user_count} notification(s)"
                ))
        
        # Summary
        self.stdout.write("\n" + "="*60)
        self.stdout.write(self.style.SUCCESS(
            f"📊 Generation Summary:"
        ))
        self.stdout.write(f"  Total schedules checked: {total_schedules}")
        self.stdout.write(f"  Schedules skipped: {skipped_count}")
        self.stdout.write(self.style.SUCCESS(
            f"  ✅ Notifications {'would be ' if dry_run else ''}created: {created_count}"
        ))
        self.stdout.write("="*60)
        
        logger.info(
            f"Generated {created_count} class schedule notifications "
            f"({skipped_count} schedules skipped)"
        )
