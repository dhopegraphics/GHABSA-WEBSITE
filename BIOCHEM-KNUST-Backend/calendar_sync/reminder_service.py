"""
Calendar Reminder Service
Handles scheduling and sending push notification reminders for calendar events.

This service addresses the limitation that many calendar apps (especially Google Calendar)
ignore VALARM reminders in subscribed iCal feeds. Instead, we use push notifications
to reliably remind users about their classes, exams, and events.
"""
from datetime import datetime, timedelta, date
from django.utils import timezone
from django.db import transaction
from django.db.models import Q
import logging
from typing import List, Optional, Dict, Any

from .models import (
    CalendarToken,
    CalendarReminderPreference,
    ScheduledCalendarReminder
)

logger = logging.getLogger(__name__)


class CalendarReminderService:
    """
    Service for managing calendar reminders via push notifications.
    
    Key features:
    - Schedules multiple reminders per event based on user preferences
    - Sends push notifications at the right time
    - Prevents duplicate reminders
    - Cleans up old/processed reminders
    """
    
    # Human-readable time descriptions
    TIME_DESCRIPTIONS = {
        5: "5 minutes",
        10: "10 minutes",
        15: "15 minutes",
        30: "30 minutes",
        60: "1 hour",
        120: "2 hours",
        180: "3 hours",
        360: "6 hours",
        720: "12 hours",
        1440: "1 day",
        2880: "2 days",
        4320: "3 days",
        10080: "1 week",
    }
    
    @classmethod
    def get_time_description(cls, minutes: int) -> str:
        """Convert minutes to human-readable description"""
        if minutes in cls.TIME_DESCRIPTIONS:
            return cls.TIME_DESCRIPTIONS[minutes]
        
        if minutes < 60:
            return f"{minutes} minutes"
        elif minutes < 1440:
            hours = minutes // 60
            return f"{hours} hour{'s' if hours > 1 else ''}"
        else:
            days = minutes // 1440
            return f"{days} day{'s' if days > 1 else ''}"
    
    @classmethod
    def schedule_class_reminders(
        cls,
        user,
        schedule,
        schedule_datetime: datetime,
    ) -> List[ScheduledCalendarReminder]:
        """
        Schedule reminders for a class session.
        
        Args:
            user: The user to remind
            schedule: ClassSchedule object
            schedule_datetime: The actual datetime of the class session
        
        Returns:
            List of created/updated ScheduledCalendarReminder objects
        """
        prefs = CalendarReminderPreference.get_for_user(user)
        
        if not prefs.class_reminders_enabled or not prefs.push_reminders_enabled:
            return []
        
        reminder_times = prefs.get_reminder_times('class')
        reminders = []
        
        course_code = schedule.course.course_code if schedule.course else "Class"
        course_name = schedule.course.course_name if schedule.course else "Unknown"
        
        for minutes_before in reminder_times:
            time_desc = cls.get_time_description(minutes_before)
            
            title = f"📚 Class in {time_desc}"
            message = f"{course_code}: {course_name}\n"
            
            if schedule.room:
                message += f"📍 Room: {schedule.room}\n"
            message += f"⏰ Starts at {schedule_datetime.strftime('%I:%M %p')}"
            
            reminder = ScheduledCalendarReminder.schedule_reminder(
                user=user,
                reminder_type='class',
                reference_model='ClassSchedule',
                reference_id=str(schedule.id),
                title=title,
                message=message,
                event_datetime=schedule_datetime,
                minutes_before=minutes_before
            )
            
            if reminder:
                reminders.append(reminder)
        
        return reminders
    
    @classmethod
    def schedule_exam_reminders(
        cls,
        user,
        exam,
    ) -> List[ScheduledCalendarReminder]:
        """
        Schedule reminders for an exam.
        
        Args:
            user: The user to remind
            exam: ExaminationSchedule object
        
        Returns:
            List of created/updated ScheduledCalendarReminder objects
        """
        if not exam.time:
            return []
        
        prefs = CalendarReminderPreference.get_for_user(user)
        
        if not prefs.exam_reminders_enabled or not prefs.push_reminders_enabled:
            return []
        
        reminder_times = prefs.get_reminder_times('exam')
        reminders = []
        
        course_code = exam.course.course_code if exam.course else "Exam"
        course_name = exam.course.course_name if exam.course else "Unknown"
        exam_datetime = exam.time
        
        for minutes_before in reminder_times:
            time_desc = cls.get_time_description(minutes_before)
            
            # More urgent titles for closer reminders
            if minutes_before >= 1440:
                title = f"📝 Exam in {time_desc}"
            elif minutes_before >= 120:
                title = f"⚠️ Exam in {time_desc}"
            else:
                title = f"🚨 EXAM in {time_desc}!"
            
            message = f"{course_code}: {course_name}\n"
            message += f"📍 {exam.college}"
            if exam.room:
                message += f", Room {exam.room}"
            message += f"\n⏰ {exam_datetime.strftime('%a, %b %d at %I:%M %p')}"
            
            reminder = ScheduledCalendarReminder.schedule_reminder(
                user=user,
                reminder_type='exam',
                reference_model='ExaminationSchedule',
                reference_id=str(exam.id),
                title=title,
                message=message,
                event_datetime=exam_datetime,
                minutes_before=minutes_before
            )
            
            if reminder:
                reminders.append(reminder)
        
        return reminders
    
    @classmethod
    def schedule_event_reminders(
        cls,
        user,
        event,
    ) -> List[ScheduledCalendarReminder]:
        """
        Schedule reminders for an event.
        
        Args:
            user: The user to remind (for RSVP'd events)
            event: Event object
        
        Returns:
            List of created/updated ScheduledCalendarReminder objects
        """
        if not event.event_date:
            return []
        
        prefs = CalendarReminderPreference.get_for_user(user)
        
        if not prefs.event_reminders_enabled or not prefs.push_reminders_enabled:
            return []
        
        reminder_times = prefs.get_reminder_times('event')
        reminders = []
        
        event_datetime = event.event_date
        
        for minutes_before in reminder_times:
            time_desc = cls.get_time_description(minutes_before)
            
            emoji = event.emoji or "📅"
            title = f"{emoji} Event in {time_desc}"
            
            message = f"{event.event_name}\n"
            if event.venue:
                message += f"📍 {event.venue}\n"
            message += f"⏰ {event_datetime.strftime('%a, %b %d at %I:%M %p')}"
            
            reminder = ScheduledCalendarReminder.schedule_reminder(
                user=user,
                reminder_type='event',
                reference_model='Event',
                reference_id=str(event.event_id),
                title=title,
                message=message,
                event_datetime=event_datetime,
                minutes_before=minutes_before
            )
            
            if reminder:
                reminders.append(reminder)
        
        return reminders
    
    @classmethod
    def schedule_all_class_reminders_for_day(
        cls,
        target_date: date = None,
        days_ahead: int = 2
    ) -> Dict[str, int]:
        """
        Schedule class reminders for all users for a specific day or range.
        This should be run daily via Celery beat.
        
        Args:
            target_date: The date to schedule reminders for (defaults to today)
            days_ahead: How many days ahead to schedule (default 2)
        
        Returns:
            Dict with scheduling statistics
        """
        from timetable_system.models import ClassSchedule
        from accounts.models import CustomUser
        import pytz
        
        TIMEZONE = pytz.timezone('Africa/Accra')
        target_date = target_date or timezone.now().date()
        stats = {'users_processed': 0, 'reminders_scheduled': 0, 'errors': 0}
        
        # Get users who have synced (have calendar tokens)
        users_with_tokens = CalendarToken.objects.filter(
            is_active=True
        ).values_list('user_id', flat=True).distinct()
        
        users = CustomUser.objects.filter(
            id__in=users_with_tokens,
            program__isnull=False
        )
        
        logger.info(f"Scheduling class reminders for {users.count()} users, dates: {target_date} to {target_date + timedelta(days=days_ahead)}")
        
        for user in users:
            try:
                # Get user's schedules
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
                
                # Schedule reminders for each day
                for day_offset in range(days_ahead + 1):
                    check_date = target_date + timedelta(days=day_offset)
                    check_day = check_date.isoweekday()
                    
                    for schedule in schedules.filter(day_of_week=check_day):
                        schedule_datetime = TIMEZONE.localize(
                            datetime.combine(check_date, schedule.start_time)
                        )
                        
                        # Only schedule for future classes
                        if schedule_datetime <= timezone.now():
                            continue
                        
                        reminders = cls.schedule_class_reminders(
                            user=user,
                            schedule=schedule,
                            schedule_datetime=schedule_datetime
                        )
                        stats['reminders_scheduled'] += len(reminders)
                
                stats['users_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error scheduling reminders for user {user.id}: {e}")
                stats['errors'] += 1
        
        logger.info(f"Class reminder scheduling complete: {stats}")
        return stats
    
    @classmethod
    def schedule_all_exam_reminders(cls) -> Dict[str, int]:
        """
        Schedule exam reminders for all users with upcoming exams.
        This should be run daily via Celery beat.
        
        Returns:
            Dict with scheduling statistics
        """
        from timetable_system.models import ExaminationSchedule
        from accounts.models import CustomUser
        
        stats = {'users_processed': 0, 'reminders_scheduled': 0, 'errors': 0}
        
        # Get upcoming exams (next 14 days)
        now = timezone.now()
        upcoming_limit = now + timedelta(days=14)
        
        exams = ExaminationSchedule.objects.filter(
            time__gte=now,
            time__lte=upcoming_limit
        ).select_related('course')
        
        if not exams.exists():
            logger.info("No upcoming exams found")
            return stats
        
        # Get users who have synced
        users_with_tokens = CalendarToken.objects.filter(
            is_active=True
        ).values_list('user_id', flat=True).distinct()
        
        users = CustomUser.objects.filter(
            id__in=users_with_tokens,
            program__isnull=False
        )
        
        logger.info(f"Scheduling exam reminders for {users.count()} users, {exams.count()} exams")
        
        for user in users:
            try:
                year = user.get_year()
                semester = user.calculate_current_semester()
                
                # Get exams for this user's year and semester
                user_exams = exams.filter(
                    course__year=year,
                    course__semester=semester
                )
                
                for exam in user_exams:
                    reminders = cls.schedule_exam_reminders(user=user, exam=exam)
                    stats['reminders_scheduled'] += len(reminders)
                
                stats['users_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error scheduling exam reminders for user {user.id}: {e}")
                stats['errors'] += 1
        
        logger.info(f"Exam reminder scheduling complete: {stats}")
        return stats
    
    @classmethod
    def schedule_event_reminders_for_rsvps(cls) -> Dict[str, int]:
        """
        Schedule event reminders for users who have RSVP'd.
        This should be run daily via Celery beat.
        
        Returns:
            Dict with scheduling statistics
        """
        from events.models import Event, EventRSVP
        
        stats = {'users_processed': 0, 'reminders_scheduled': 0, 'errors': 0}
        
        # Get upcoming events (next 7 days)
        now = timezone.now()
        upcoming_limit = now + timedelta(days=7)
        
        # Get RSVPs for upcoming events
        rsvps = EventRSVP.objects.filter(
            event__event_date__gte=now,
            event__event_date__lte=upcoming_limit,
            status='attending'
        ).select_related('event', 'user')
        
        logger.info(f"Scheduling event reminders for {rsvps.count()} RSVPs")
        
        processed_users = set()
        
        for rsvp in rsvps:
            try:
                user = rsvp.user
                event = rsvp.event
                
                # Check if user has calendar sync enabled
                if not CalendarToken.objects.filter(user=user, is_active=True).exists():
                    continue
                
                reminders = cls.schedule_event_reminders(user=user, event=event)
                stats['reminders_scheduled'] += len(reminders)
                
                if user.id not in processed_users:
                    processed_users.add(user.id)
                    stats['users_processed'] += 1
                
            except Exception as e:
                logger.error(f"Error scheduling event reminder for RSVP {rsvp.id}: {e}")
                stats['errors'] += 1
        
        logger.info(f"Event reminder scheduling complete: {stats}")
        return stats
    
    @classmethod
    def process_pending_reminders(cls) -> Dict[str, int]:
        """
        Process and send all pending reminders that are due.
        This should be run every 1-5 minutes via Celery beat.
        
        Returns:
            Dict with processing statistics
        """
        from notifications.services import PushNotificationService
        
        stats = {'processed': 0, 'sent': 0, 'failed': 0, 'skipped': 0}
        
        now = timezone.now()
        
        # Get pending reminders that are due (within the last 10 minutes to now)
        # We use a small window to catch any reminders that might have been missed
        window_start = now - timedelta(minutes=10)
        
        pending_reminders = ScheduledCalendarReminder.objects.filter(
            status='pending',
            remind_at__lte=now,
            remind_at__gte=window_start
        ).select_related('user')
        
        logger.info(f"Processing {pending_reminders.count()} pending reminders")
        
        for reminder in pending_reminders:
            stats['processed'] += 1
            
            try:
                # Check if user still has push reminders enabled
                try:
                    prefs = reminder.user.calendar_reminder_preferences
                    if not prefs.push_reminders_enabled:
                        reminder.status = 'skipped'
                        reminder.save(update_fields=['status', 'updated_at'])
                        stats['skipped'] += 1
                        continue
                except CalendarReminderPreference.DoesNotExist:
                    pass  # Continue with default behavior
                
                # Send push notification
                result = PushNotificationService.send_push_notification(
                    user=reminder.user,
                    title=reminder.title,
                    body=reminder.message,
                    data={
                        'type': 'calendar_reminder',
                        'reminder_type': reminder.reminder_type,
                        'reference_model': reminder.reference_model,
                        'reference_id': reminder.reference_id,
                        'event_datetime': reminder.event_datetime.isoformat(),
                    },
                    priority='high',
                    sound='default',
                )
                
                if result.get('success'):
                    reminder.status = 'sent'
                    reminder.sent_at = now
                    stats['sent'] += 1
                else:
                    reminder.status = 'failed'
                    reminder.error_message = result.get('error', 'Unknown error')
                    stats['failed'] += 1
                
                reminder.save(update_fields=['status', 'sent_at', 'error_message', 'updated_at'])
                
            except Exception as e:
                logger.error(f"Error processing reminder {reminder.id}: {e}")
                reminder.status = 'failed'
                reminder.error_message = str(e)
                reminder.save(update_fields=['status', 'error_message', 'updated_at'])
                stats['failed'] += 1
        
        logger.info(f"Reminder processing complete: {stats}")
        return stats
    
    @classmethod
    def cleanup_old_reminders(cls, days_old: int = 7) -> int:
        """
        Delete old processed reminders to keep the database clean.
        
        Args:
            days_old: Delete reminders older than this many days
        
        Returns:
            Number of deleted reminders
        """
        cutoff = timezone.now() - timedelta(days=days_old)
        
        deleted_count, _ = ScheduledCalendarReminder.objects.filter(
            status__in=['sent', 'skipped', 'failed'],
            created_at__lt=cutoff
        ).delete()
        
        logger.info(f"Cleaned up {deleted_count} old reminders")
        return deleted_count
    
    @classmethod
    def get_user_upcoming_reminders(
        cls,
        user,
        reminder_type: str = None,
        limit: int = 20
    ) -> List[ScheduledCalendarReminder]:
        """
        Get upcoming reminders for a user.
        
        Args:
            user: The user
            reminder_type: Optional filter by type ('class', 'exam', 'event')
            limit: Maximum number of reminders to return
        
        Returns:
            List of ScheduledCalendarReminder objects
        """
        filters = {
            'user': user,
            'status': 'pending',
            'remind_at__gte': timezone.now()
        }
        
        if reminder_type:
            filters['reminder_type'] = reminder_type
        
        return list(
            ScheduledCalendarReminder.objects.filter(**filters)
            .order_by('remind_at')[:limit]
        )
