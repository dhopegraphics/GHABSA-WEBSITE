"""
Management command to generate exam schedule notifications
This command should be run daily (e.g., 6:00 AM) to create notifications for upcoming exams

Usage:
    python manage.py generate_exam_notifications
    python manage.py generate_exam_notifications --dry-run
    python manage.py generate_exam_notifications --days 7
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from notifications.models import NotificationTrigger, PushNotification
from timetable_system.models import ExaminationSchedule
from accounts.models import CustomUser
from accounts.repository import UserRepository
from notifications.services import NotificationScheduler
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate push notifications for upcoming exam schedules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=7,
            help='Number of days ahead to check (default: 7)'
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        days_ahead = options['days']
        
        self.stdout.write(self.style.WARNING(
            f"🔍 Generating exam schedule notifications for next {days_ahead} day(s)..."
        ))
        
        # Get active triggers for exam schedules
        triggers = NotificationTrigger.objects.filter(
            trigger_type='exam_schedule',
            is_active=True
        ).select_related('template')
        
        if not triggers.exists():
            self.stdout.write(self.style.ERROR(
                "❌ No active exam schedule triggers found. "
                "Please create notification triggers in Django Admin."
            ))
            return
        
        self.stdout.write(f"Found {triggers.count()} active trigger(s)")
        
        created_count = 0
        skipped_count = 0
        now = timezone.now()
        
        # Get upcoming exams
        upcoming_exams = ExaminationSchedule.objects.filter(
            time__gte=now,
            time__lte=now + timedelta(days=days_ahead)
        ).select_related('course').order_by('time')
        
        total_exams = upcoming_exams.count()
        self.stdout.write(f"Found {total_exams} upcoming exam(s)")
        
        for exam in upcoming_exams:
            self.stdout.write(
                f"\n📝 Exam: {exam.course.course_code} - "
                f"{exam.time.strftime('%A, %Y-%m-%d %H:%M')}"
            )
            self.stdout.write(
                f"   Index range: {exam.index_number_start} - {exam.index_number_end}"
            )
            
            # Get students for this exam using repository
            students = UserRepository.fetch_examination_students_phone(
                year=exam.course.year,
                index_number_start=exam.index_number_start,
                index_number_end=exam.index_number_end,
            )
            
            if not students:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(
                    "  ⚠️  No students found for this exam, skipping"
                ))
                continue
            
            # Get user objects
            phone_numbers = [str(s) for s in students]
            users = CustomUser.objects.filter(
                phone__in=phone_numbers,
                is_active=True,
                notification_preferences__exam_reminders=True,
                notification_preferences__push_enabled=True,
            ).distinct()
            
            user_count = users.count()
            self.stdout.write(f"  Target users: {user_count}")
            
            if user_count == 0:
                skipped_count += 1
                self.stdout.write(self.style.WARNING(
                    "  ⚠️  No active users with exam notifications enabled, skipping"
                ))
                continue
            
            for trigger in triggers:
                notification_time = trigger.calculate_notification_time(exam.time)
                
                # Only create notifications for future times
                if notification_time <= now:
                    self.stdout.write(
                        f"  ⏭️  Skipping trigger '{trigger.name}' "
                        f"(notification time {notification_time} is in the past)"
                    )
                    continue
                
                # Prepare context for template
                context = {
                    'course_name': exam.course.course_name,
                    'course_code': exam.course.course_code,
                    'exam_date': exam.time.strftime('%A, %B %d, %Y'),
                    'exam_time': exam.time.strftime('%I:%M %p'),
                    'college': exam.college,
                    'room': exam.room or 'TBA',
                    'index_start': exam.index_number_start,
                    'index_end': exam.index_number_end,
                    'exam_id': str(exam.id),
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
                for user in users:
                    # Check if notification already exists
                    exists = PushNotification.objects.filter(
                        user=user,
                        trigger_type='exam_schedule',
                        trigger_id=str(exam.id),
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
                        trigger_type='exam_schedule',
                        trigger_id=str(exam.id),
                        data=rendered.get('data', {}),
                        sound=rendered.get('sound', 'default'),
                        priority=rendered.get('priority', 'high'),  # Exams are high priority
                        badge=rendered.get('badge', 1),
                        category=rendered.get('category', 'exam'),
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
        self.stdout.write(f"  Total exams checked: {total_exams}")
        self.stdout.write(f"  Exams skipped: {skipped_count}")
        self.stdout.write(self.style.SUCCESS(
            f"  ✅ Notifications {'would be ' if dry_run else ''}created: {created_count}"
        ))
        self.stdout.write("="*60)
        
        logger.info(
            f"Generated {created_count} exam schedule notifications "
            f"({skipped_count} exams skipped)"
        )
