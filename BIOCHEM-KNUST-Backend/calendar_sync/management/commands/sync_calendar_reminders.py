"""
Management command to sync and process calendar reminders.
Useful for testing and manual trigger.

Usage:
    python manage.py sync_calendar_reminders --all
    python manage.py sync_calendar_reminders --user <username>
    python manage.py sync_calendar_reminders --process
    python manage.py sync_calendar_reminders --cleanup
"""
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone


class Command(BaseCommand):
    help = 'Sync and process calendar reminders'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--all',
            action='store_true',
            help='Schedule all reminders (classes, exams, events)'
        )
        parser.add_argument(
            '--classes',
            action='store_true',
            help='Schedule class reminders only'
        )
        parser.add_argument(
            '--exams',
            action='store_true',
            help='Schedule exam reminders only'
        )
        parser.add_argument(
            '--events',
            action='store_true',
            help='Schedule event reminders only'
        )
        parser.add_argument(
            '--user',
            type=str,
            help='Sync reminders for a specific user (by username)'
        )
        parser.add_argument(
            '--process',
            action='store_true',
            help='Process and send pending reminders'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Cleanup old reminders'
        )
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show reminder statistics'
        )
    
    def handle(self, *args, **options):
        from calendar_sync.reminder_service import CalendarReminderService
        from calendar_sync.models import ScheduledCalendarReminder, CalendarReminderPreference
        
        if options['stats']:
            self._show_stats()
            return
        
        if options['process']:
            self.stdout.write('Processing pending reminders...')
            results = CalendarReminderService.process_pending_reminders()
            self.stdout.write(self.style.SUCCESS(
                f"Processed: {results['processed']}, Sent: {results['sent']}, "
                f"Failed: {results['failed']}, Skipped: {results['skipped']}"
            ))
            return
        
        if options['cleanup']:
            self.stdout.write('Cleaning up old reminders...')
            deleted = CalendarReminderService.cleanup_old_reminders(days_old=7)
            self.stdout.write(self.style.SUCCESS(f"Deleted {deleted} old reminders"))
            return
        
        if options['user']:
            self._sync_user(options['user'])
            return
        
        if options['all']:
            self._schedule_all()
            return
        
        if options['classes']:
            self.stdout.write('Scheduling class reminders...')
            results = CalendarReminderService.schedule_all_class_reminders_for_day(days_ahead=2)
            self.stdout.write(self.style.SUCCESS(
                f"Users: {results['users_processed']}, Reminders: {results['reminders_scheduled']}"
            ))
            return
        
        if options['exams']:
            self.stdout.write('Scheduling exam reminders...')
            results = CalendarReminderService.schedule_all_exam_reminders()
            self.stdout.write(self.style.SUCCESS(
                f"Users: {results['users_processed']}, Reminders: {results['reminders_scheduled']}"
            ))
            return
        
        if options['events']:
            self.stdout.write('Scheduling event reminders...')
            results = CalendarReminderService.schedule_event_reminders_for_rsvps()
            self.stdout.write(self.style.SUCCESS(
                f"Users: {results['users_processed']}, Reminders: {results['reminders_scheduled']}"
            ))
            return
        
        # Default: show help
        self.stdout.write(self.style.WARNING(
            'No action specified. Use --help to see available options.'
        ))
    
    def _sync_user(self, username):
        """Sync reminders for a specific user"""
        from accounts.models import CustomUser
        from calendar_sync.tasks import sync_user_reminders
        
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            raise CommandError(f"User '{username}' not found")
        
        self.stdout.write(f'Syncing reminders for user: {username}...')
        
        # Run synchronously (not async) for command line
        from calendar_sync.reminder_service import CalendarReminderService
        from timetable_system.models import ClassSchedule, ExaminationSchedule
        from events.models import EventRSVP
        from datetime import datetime, timedelta, date
        import pytz
        
        TIMEZONE = pytz.timezone('Africa/Accra')
        now = timezone.now()
        today = now.date()
        
        stats = {
            'class_reminders': 0,
            'exam_reminders': 0,
            'event_reminders': 0,
        }
        
        # Class reminders
        try:
            year = user.get_year()
            program = user.program
            group = user.group
            semester = user.calculate_current_semester()
            
            filters = {
                'program': program,
                'year': year,
                'course__semester': semester
            }
            
            if ClassSchedule.program_requires_group(program) and group:
                filters['group'] = group
            
            schedules = ClassSchedule.objects.filter(**filters).select_related('course')
            
            for day_offset in range(7):
                check_date = today + timedelta(days=day_offset)
                check_day = check_date.isoweekday()
                
                for schedule in schedules.filter(day_of_week=check_day):
                    schedule_datetime = TIMEZONE.localize(
                        datetime.combine(check_date, schedule.start_time)
                    )
                    
                    if schedule_datetime > now:
                        reminders = CalendarReminderService.schedule_class_reminders(
                            user=user,
                            schedule=schedule,
                            schedule_datetime=schedule_datetime
                        )
                        stats['class_reminders'] += len(reminders)
        except Exception as e:
            self.stderr.write(f"Error scheduling class reminders: {e}")
        
        # Exam reminders
        try:
            year = user.get_year()
            semester = user.calculate_current_semester()
            
            exams = ExaminationSchedule.objects.filter(
                time__gte=now,
                course__year=year,
                course__semester=semester
            ).select_related('course')
            
            for exam in exams:
                reminders = CalendarReminderService.schedule_exam_reminders(user=user, exam=exam)
                stats['exam_reminders'] += len(reminders)
        except Exception as e:
            self.stderr.write(f"Error scheduling exam reminders: {e}")
        
        # Event reminders
        try:
            rsvps = EventRSVP.objects.filter(
                user=user,
                event__event_date__gte=now,
                status='attending'
            ).select_related('event')
            
            for rsvp in rsvps:
                reminders = CalendarReminderService.schedule_event_reminders(user=user, event=rsvp.event)
                stats['event_reminders'] += len(reminders)
        except Exception as e:
            self.stderr.write(f"Error scheduling event reminders: {e}")
        
        total = sum(stats.values())
        self.stdout.write(self.style.SUCCESS(
            f"Synced {total} reminders - Classes: {stats['class_reminders']}, "
            f"Exams: {stats['exam_reminders']}, Events: {stats['event_reminders']}"
        ))
    
    def _schedule_all(self):
        """Schedule all types of reminders"""
        from calendar_sync.reminder_service import CalendarReminderService
        
        self.stdout.write('Scheduling all reminders...')
        
        self.stdout.write('  - Classes...')
        class_results = CalendarReminderService.schedule_all_class_reminders_for_day(days_ahead=2)
        
        self.stdout.write('  - Exams...')
        exam_results = CalendarReminderService.schedule_all_exam_reminders()
        
        self.stdout.write('  - Events...')
        event_results = CalendarReminderService.schedule_event_reminders_for_rsvps()
        
        total_reminders = (
            class_results.get('reminders_scheduled', 0) +
            exam_results.get('reminders_scheduled', 0) +
            event_results.get('reminders_scheduled', 0)
        )
        
        self.stdout.write(self.style.SUCCESS(f"\nTotal reminders scheduled: {total_reminders}"))
        self.stdout.write(f"  Classes: {class_results.get('reminders_scheduled', 0)}")
        self.stdout.write(f"  Exams: {exam_results.get('reminders_scheduled', 0)}")
        self.stdout.write(f"  Events: {event_results.get('reminders_scheduled', 0)}")
    
    def _show_stats(self):
        """Show reminder statistics"""
        from calendar_sync.models import ScheduledCalendarReminder, CalendarReminderPreference, CalendarToken
        from accounts.models import CustomUser
        
        now = timezone.now()
        
        # Token stats
        total_tokens = CalendarToken.objects.filter(is_active=True).count()
        users_with_tokens = CalendarToken.objects.filter(is_active=True).values('user').distinct().count()
        
        # Preference stats
        total_prefs = CalendarReminderPreference.objects.count()
        push_enabled = CalendarReminderPreference.objects.filter(push_reminders_enabled=True).count()
        
        # Reminder stats
        pending = ScheduledCalendarReminder.objects.filter(status='pending').count()
        pending_due = ScheduledCalendarReminder.objects.filter(status='pending', remind_at__lte=now).count()
        sent_today = ScheduledCalendarReminder.objects.filter(
            status='sent',
            sent_at__date=now.date()
        ).count()
        
        by_type = ScheduledCalendarReminder.objects.filter(status='pending').values('reminder_type').annotate(
            count=models.Count('id')
        )
        
        self.stdout.write(self.style.SUCCESS('\n=== Calendar Reminder Stats ===\n'))
        
        self.stdout.write(f"Users with calendar sync: {users_with_tokens}")
        self.stdout.write(f"Active tokens: {total_tokens}")
        self.stdout.write(f"Users with reminder preferences: {total_prefs}")
        self.stdout.write(f"Push notifications enabled: {push_enabled}")
        
        self.stdout.write(f"\nPending reminders: {pending}")
        self.stdout.write(f"Due now: {pending_due}")
        self.stdout.write(f"Sent today: {sent_today}")
        
        self.stdout.write('\nBy type:')
        for item in by_type:
            self.stdout.write(f"  {item['reminder_type']}: {item['count']}")


# Import for stats
from django.db import models
