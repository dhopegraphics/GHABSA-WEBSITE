"""
Celery tasks for notifications
"""
from celery import shared_task
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)


@shared_task
def process_scheduled_notifications():
    """
    Process and send all pending scheduled notifications
    This task should be run every 5-10 minutes via Celery Beat
    """
    from notifications.services import NotificationScheduler
    
    logger.info("Processing scheduled notifications...")
    results = NotificationScheduler.process_pending_notifications()
    logger.info(f"Processed: {results['processed']}, Sent: {results['sent']}, Failed: {results['failed']}")
    
    return results


@shared_task
def generate_class_schedule_notifications():
    """
    Generate notifications for upcoming class schedules
    Should be run daily or multiple times per day
    """
    from timetable_system.models import ClassSchedule
    from notifications.models import NotificationTrigger, PushNotification
    from accounts.models import CustomUser
    from notifications.services import NotificationScheduler
    from django.db.models import Q
    
    logger.info("Generating class schedule notifications...")
    
    # Get active triggers for class schedules
    triggers = NotificationTrigger.objects.filter(
        trigger_type='class_schedule',
        is_active=True
    ).select_related('template')
    
    if not triggers.exists():
        logger.info("No active class schedule triggers found")
        return {'created': 0}
    
    created_count = 0
    now = timezone.now()
    today = now.date()
    
    # Get today's day of week (1=Monday, 7=Sunday)
    current_day = now.isoweekday()
    
    # Get all schedules for today and tomorrow
    schedules = ClassSchedule.objects.filter(
        day_of_week__in=[current_day, current_day + 1 if current_day < 7 else 1]
    ).select_related('course')
    
    for schedule in schedules:
        # Determine the actual date for this schedule
        if schedule.day_of_week == current_day:
            schedule_date = today
        else:
            schedule_date = today + timedelta(days=1)
        
        # Combine date and time
        schedule_datetime = timezone.make_aware(
            timezone.datetime.combine(schedule_date, schedule.start_time)
        )
        
        # Skip if schedule is in the past
        if schedule_datetime <= now:
            continue
        
        # Get users for this schedule based on program and year
        # Only filter by group if the program requires groups (e.g., CS)
        users_filter = {
            'program': schedule.program,
            'graduation_year__isnull': False,
        }
        
        # Only add group filter for programs that require groups
        from timetable_system.models import ClassSchedule
        if ClassSchedule.program_requires_group(schedule.program) and schedule.group:
            users_filter['group'] = schedule.group
        
        users = CustomUser.objects.filter(**users_filter)
        
        # Filter by year (user.year returns year 1-4, schedule.year is 1-4)
        valid_users = []
        for user in users:
            if user.year == schedule.year:  # Both are year values (1-4)
                # Check notification preferences
                try:
                    if (user.notification_preferences.class_reminders and 
                        user.notification_preferences.push_enabled):
                        valid_users.append(user)
                except:
                    pass  # User doesn't have preferences yet
        
        users = valid_users
        
        for trigger in triggers:
            notification_time = trigger.calculate_notification_time(schedule_datetime)
            
            # Only create notifications for future times
            if notification_time <= now:
                continue
            
            # Check if conditions match
            conditions_match = True
            if trigger.conditions:
                if 'day_of_week' in trigger.conditions:
                    if schedule.day_of_week not in trigger.conditions['day_of_week']:
                        conditions_match = False
                if 'program' in trigger.conditions:
                    if schedule.program not in trigger.conditions['program']:
                        conditions_match = False
            
            if not conditions_match:
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
                'group': schedule.get_group_display() if schedule.group else 'All',
                'schedule_id': str(schedule.id),
            }
            
            # Render notification from template
            rendered = trigger.template.render(context)
            
            # Create notifications for each user
            for user in users:
                # Check if notification already exists
                existing = PushNotification.objects.filter(
                    user=user,
                    trigger_type='class_schedule',
                    trigger_id=str(schedule.id),
                    scheduled_at=notification_time,
                    status__in=['scheduled', 'sent']
                ).exists()
                
                if not existing:
                    NotificationScheduler.schedule_notification(
                        user=user,
                        title=rendered['title'],
                        body=rendered['body'],
                        scheduled_at=notification_time,
                        template=trigger.template,
                        trigger_type='class_schedule',
                        trigger_id=str(schedule.id),
                        data=rendered['data'],
                        sound=rendered['sound'],
                        priority=rendered['priority'],
                        badge=rendered['badge'],
                        category=rendered['category'],
                    )
                    created_count += 1
    
    logger.info(f"Created {created_count} class schedule notifications")
    return {'created': created_count}


@shared_task
def generate_exam_schedule_notifications():
    """
    Generate notifications for upcoming exam schedules
    Should be run daily
    """
    from timetable_system.models import ExaminationSchedule
    from notifications.models import NotificationTrigger, PushNotification
    from accounts.repository import UserRepository
    from notifications.services import NotificationScheduler
    from django.db.models import Q
    
    logger.info("Generating exam schedule notifications...")
    
    # Get active triggers for exam schedules
    triggers = NotificationTrigger.objects.filter(
        trigger_type='exam_schedule',
        is_active=True
    ).select_related('template')
    
    if not triggers.exists():
        logger.info("No active exam schedule triggers found")
        return {'created': 0}
    
    created_count = 0
    now = timezone.now()
    
    # Get upcoming exams (next 7 days)
    upcoming_exams = ExaminationSchedule.objects.filter(
        time__gte=now,
        time__lte=now + timedelta(days=7)
    ).select_related('course')
    
    for exam in upcoming_exams:
        # Get students for this exam
        students = UserRepository.fetch_examination_students_phone(
            year=exam.course.year,
            index_number_start=exam.index_number_start,
            index_number_end=exam.index_number_end,
        )
        
        if not students:
            continue
        
        # Get user objects
        from accounts.models import CustomUser
        phone_numbers = [str(s) for s in students]
        users = CustomUser.objects.filter(
            phone__in=phone_numbers,
            notification_preferences__exam_reminders=True,
            notification_preferences__push_enabled=True,
        ).distinct()
        
        for trigger in triggers:
            notification_time = trigger.calculate_notification_time(exam.time)
            
            # Only create notifications for future times
            if notification_time <= now:
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
            
            # Create notifications for each user
            for user in users:
                # Check if notification already exists
                existing = PushNotification.objects.filter(
                    user=user,
                    trigger_type='exam_schedule',
                    trigger_id=str(exam.id),
                    scheduled_at=notification_time,
                    status__in=['scheduled', 'sent']
                ).exists()
                
                if not existing:
                    NotificationScheduler.schedule_notification(
                        user=user,
                        title=rendered['title'],
                        body=rendered['body'],
                        scheduled_at=notification_time,
                        template=trigger.template,
                        trigger_type='exam_schedule',
                        trigger_id=str(exam.id),
                        data=rendered['data'],
                        sound=rendered['sound'],
                        priority=rendered['priority'],
                        badge=rendered['badge'],
                        category=rendered['category'],
                    )
                    created_count += 1
    
    logger.info(f"Created {created_count} exam schedule notifications")
    return {'created': created_count}


@shared_task
def cleanup_old_notifications(days=30):
    """
    Clean up old sent/failed notifications
    Should be run weekly
    """
    from notifications.models import PushNotification
    
    cutoff_date = timezone.now() - timedelta(days=days)
    
    deleted = PushNotification.objects.filter(
        status__in=['sent', 'failed', 'cancelled'],
        created_at__lt=cutoff_date
    ).delete()
    
    logger.info(f"Cleaned up {deleted[0]} old notifications")
    return {'deleted': deleted[0]}
