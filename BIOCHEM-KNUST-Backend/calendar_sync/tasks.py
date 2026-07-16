"""
Celery Tasks for Calendar Sync
Handles scheduling and sending calendar reminders via push notifications.
"""
from celery import shared_task
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)


@shared_task(name='calendar_sync.process_calendar_reminders')
def process_calendar_reminders():
    """
    Process and send all pending calendar reminders.
    
    This task should be run every 1-5 minutes via Celery Beat to ensure
    reminders are sent on time.
    
    Example Celery Beat config:
    CELERY_BEAT_SCHEDULE = {
        'process-calendar-reminders': {
            'task': 'calendar_sync.process_calendar_reminders',
            'schedule': crontab(minute='*/2'),  # Every 2 minutes
        },
    }
    """
    from calendar_sync.reminder_service import CalendarReminderService
    
    logger.info("Processing calendar reminders...")
    results = CalendarReminderService.process_pending_reminders()
    logger.info(f"Processed: {results['processed']}, Sent: {results['sent']}, Failed: {results['failed']}")
    
    return results


@shared_task(name='calendar_sync.schedule_class_reminders')
def schedule_class_reminders():
    """
    Schedule class reminders for the next 2 days.
    
    This task should be run multiple times daily (e.g., every 6 hours)
    to schedule reminders for upcoming classes.
    
    Example Celery Beat config:
    CELERY_BEAT_SCHEDULE = {
        'schedule-class-reminders': {
            'task': 'calendar_sync.schedule_class_reminders',
            'schedule': crontab(hour='*/6'),  # Every 6 hours
        },
    }
    """
    from calendar_sync.reminder_service import CalendarReminderService
    
    logger.info("Scheduling class reminders...")
    results = CalendarReminderService.schedule_all_class_reminders_for_day(days_ahead=2)
    logger.info(f"Users: {results['users_processed']}, Reminders: {results['reminders_scheduled']}")
    
    return results


@shared_task(name='calendar_sync.schedule_exam_reminders')
def schedule_exam_reminders():
    """
    Schedule exam reminders for upcoming exams.
    
    This task should be run daily to ensure exam reminders are scheduled
    well in advance.
    
    Example Celery Beat config:
    CELERY_BEAT_SCHEDULE = {
        'schedule-exam-reminders': {
            'task': 'calendar_sync.schedule_exam_reminders',
            'schedule': crontab(hour='6', minute='0'),  # Daily at 6 AM
        },
    }
    """
    from calendar_sync.reminder_service import CalendarReminderService
    
    logger.info("Scheduling exam reminders...")
    results = CalendarReminderService.schedule_all_exam_reminders()
    logger.info(f"Users: {results['users_processed']}, Reminders: {results['reminders_scheduled']}")
    
    return results


@shared_task(name='calendar_sync.schedule_event_reminders')
def schedule_event_reminders():
    """
    Schedule event reminders for users who have RSVP'd.
    
    This task should be run daily to ensure event reminders are scheduled.
    
    Example Celery Beat config:
    CELERY_BEAT_SCHEDULE = {
        'schedule-event-reminders': {
            'task': 'calendar_sync.schedule_event_reminders',
            'schedule': crontab(hour='6', minute='30'),  # Daily at 6:30 AM
        },
    }
    """
    from calendar_sync.reminder_service import CalendarReminderService
    
    logger.info("Scheduling event reminders...")
    results = CalendarReminderService.schedule_event_reminders_for_rsvps()
    logger.info(f"Users: {results['users_processed']}, Reminders: {results['reminders_scheduled']}")
    
    return results


@shared_task(name='calendar_sync.cleanup_old_reminders')
def cleanup_old_reminders():
    """
    Clean up old processed reminders.
    
    This task should be run daily to keep the database clean.
    
    Example Celery Beat config:
    CELERY_BEAT_SCHEDULE = {
        'cleanup-old-reminders': {
            'task': 'calendar_sync.cleanup_old_reminders',
            'schedule': crontab(hour='3', minute='0'),  # Daily at 3 AM
        },
    }
    """
    from calendar_sync.reminder_service import CalendarReminderService
    
    logger.info("Cleaning up old reminders...")
    deleted = CalendarReminderService.cleanup_old_reminders(days_old=7)
    logger.info(f"Deleted {deleted} old reminders")
    
    return {'deleted': deleted}


@shared_task(name='calendar_sync.schedule_all_reminders')
def schedule_all_reminders():
    """
    Convenience task to schedule all types of reminders at once.
    
    This can be run instead of the individual scheduling tasks.
    
    Example Celery Beat config:
    CELERY_BEAT_SCHEDULE = {
        'schedule-all-reminders': {
            'task': 'calendar_sync.schedule_all_reminders',
            'schedule': crontab(hour='*/4'),  # Every 4 hours
        },
    }
    """
    from calendar_sync.reminder_service import CalendarReminderService
    
    logger.info("Scheduling all reminders...")
    
    results = {
        'classes': CalendarReminderService.schedule_all_class_reminders_for_day(days_ahead=2),
        'exams': CalendarReminderService.schedule_all_exam_reminders(),
        'events': CalendarReminderService.schedule_event_reminders_for_rsvps(),
    }
    
    total_scheduled = sum(r.get('reminders_scheduled', 0) for r in results.values())
    logger.info(f"Total reminders scheduled: {total_scheduled}")
    
    return results


@shared_task(name='calendar_sync.sync_user_reminders')
def sync_user_reminders(user_id: str):
    """
    Schedule all reminders for a specific user.
    
    This can be called when a user first syncs their calendar or
    updates their reminder preferences.
    
    Args:
        user_id: The user's ID
    """
    from accounts.models import CustomUser
    from calendar_sync.reminder_service import CalendarReminderService
    from timetable_system.models import ClassSchedule, ExaminationSchedule
    from events.models import EventRSVP
    from datetime import datetime, timedelta, date
    import pytz
    
    TIMEZONE = pytz.timezone('Africa/Accra')
    
    logger.info(f"Syncing reminders for user {user_id}...")
    
    try:
        user = CustomUser.objects.get(id=user_id)
    except CustomUser.DoesNotExist:
        logger.error(f"User {user_id} not found")
        return {'error': 'User not found'}
    
    stats = {
        'class_reminders': 0,
        'exam_reminders': 0,
        'event_reminders': 0,
    }
    
    now = timezone.now()
    today = now.date()
    
    # Schedule class reminders for the next 7 days
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
        logger.error(f"Error scheduling class reminders for user {user_id}: {e}")
    
    # Schedule exam reminders
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
        logger.error(f"Error scheduling exam reminders for user {user_id}: {e}")
    
    # Schedule event reminders for RSVPs
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
        logger.error(f"Error scheduling event reminders for user {user_id}: {e}")
    
    total = sum(stats.values())
    logger.info(f"Synced {total} reminders for user {user_id}: {stats}")
    
    return stats
