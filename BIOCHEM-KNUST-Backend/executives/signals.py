"""
Signal handlers for meeting notifications.
Sends email and SMS to all expected attendees when a meeting is created.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.conf import settings
from .models import Meeting
from utils.utils import send_email_notification, send_sms_message, normalize_phone
from notifications.services import PushNotificationService
import logging
import threading

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Meeting)
def send_meeting_notifications(sender, instance, created, **kwargs):
    """
    Send notifications to all expected attendees when a meeting is created.
    Notifications include:
    - Email with meeting details and link
    - SMS with brief meeting info
    - Push notification to mobile devices
    """
    if not created:
        return
    
    # Skip if meeting is cancelled or already completed
    if instance.status in ['cancelled', 'completed']:
        return
    
    # Use thread to not block the response
    thread = threading.Thread(
        target=_send_meeting_notifications_async,
        args=(instance.meeting_id,)
    )
    thread.daemon = True
    thread.start()


def _send_meeting_notifications_async(meeting_id):
    """
    Async worker to send meeting notifications.
    Runs in a separate thread to not block the main request.
    """
    from .models import Meeting
    import time
    
    # Small delay to ensure meeting is fully saved
    time.sleep(1)
    
    try:
        meeting = Meeting.objects.get(meeting_id=meeting_id)
    except Meeting.DoesNotExist:
        logger.error(f"Meeting {meeting_id} not found for notifications")
        return
    
    # Get all expected attendees
    attendees = meeting.expected_attendees
    
    if not attendees:
        logger.info(f"No attendees to notify for meeting: {meeting.title}")
        return
    
    logger.info(f"Sending notifications to {len(attendees)} attendees for meeting: {meeting.title}")
    
    # Track notification results
    results = {
        'email_sent': 0,
        'email_failed': 0,
        'sms_sent': 0,
        'sms_failed': 0,
        'push_sent': 0,
        'push_failed': 0,
    }
    
    for user in attendees:
        # Send email notification
        email_result = _send_meeting_email(user, meeting)
        if email_result:
            results['email_sent'] += 1
        else:
            results['email_failed'] += 1
        
        # Send SMS notification
        sms_result = _send_meeting_sms(user, meeting)
        if sms_result:
            results['sms_sent'] += 1
        else:
            results['sms_failed'] += 1
        
        # Send push notification
        push_result = _send_meeting_push(user, meeting)
        if push_result:
            results['push_sent'] += 1
        else:
            results['push_failed'] += 1
    
    logger.info(f"Meeting notification results for '{meeting.title}': {results}")


def _send_meeting_email(user, meeting):
    """
    Send meeting notification email to a user.
    """
    # Get user's email
    email = getattr(user, 'personal_email', None) or getattr(user, 'student_email', None) or getattr(user, 'email', None)
    
    if not email:
        logger.debug(f"No email for user {user.phone or user.student_id}")
        return False
    
    # Prepare context
    context = {
        'user_name': user.first_name or user.get_full_name() or 'Member',
        'meeting_title': meeting.title,
        'meeting_description': meeting.description,
        'meeting_type': meeting.get_meeting_type_display(),
        'meeting_date': meeting.scheduled_date,
        'meeting_time': meeting.scheduled_time,
        'meeting_end_time': meeting.end_time,
        'duration_minutes': meeting.duration_minutes,
        'venue': meeting.venue,
        'virtual_link': meeting.virtual_link,
        'is_virtual': meeting.is_virtual,
        'is_hybrid': meeting.is_hybrid,
        'committee_name': meeting.committee.name if meeting.committee else None,
        'is_executive_meeting': meeting.is_executive_meeting,
        'organizer_name': meeting.created_by.get_full_name() if meeting.created_by else 'CSS Executive',
        'office_year': meeting.office_year,
    }
    
    subject = f"📅 Meeting Invitation: {meeting.title}"
    
    try:
        success, message = send_email_notification(
            recipient_email=email,
            subject=subject,
            template_name='executives/meeting_notification_email.html',
            context=context,
        )
        
        if success:
            logger.debug(f"Email sent to {email} for meeting {meeting.title}")
        else:
            logger.warning(f"Email failed to {email}: {message}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending meeting email to {email}: {str(e)}")
        return False


def _send_meeting_sms(user, meeting):
    """
    Send meeting notification SMS to a user.
    """
    # Get user's phone number
    phone = getattr(user, 'phone', None)
    
    if not phone:
        logger.debug(f"No phone for user {user.student_id or user.pk}")
        return False
    
    # Convert PhoneNumber object to string and normalize
    phone = str(phone) if phone else None
    if not phone:
        return False
    phone = normalize_phone(phone)
    
    # Format date and time
    date_str = meeting.scheduled_date.strftime('%b %d, %Y')
    time_str = meeting.scheduled_time.strftime('%I:%M %p')
    
    # Determine location
    if meeting.is_virtual:
        location = "Virtual Meeting"
    elif meeting.is_hybrid:
        location = f"{meeting.venue} / Virtual"
    else:
        location = meeting.venue or "TBA"
    
    # Prepare context for SMS template
    context = {
        'meeting_title': meeting.title[:50],  # Truncate for SMS
        'meeting_date': date_str,
        'meeting_time': time_str,
        'location': location[:30],  # Truncate location
        'meeting_type': meeting.get_meeting_type_display(),
    }
    
    try:
        success, message = send_sms_message(
            phone=phone,
            template='executives/meeting_notification_sms.txt',
            context=context,
            is_otp=False,
        )
        
        if success:
            logger.debug(f"SMS sent to {phone} for meeting {meeting.title}")
        else:
            logger.warning(f"SMS failed to {phone}: {message}")
        
        return success
        
    except Exception as e:
        logger.error(f"Error sending meeting SMS to {phone}: {str(e)}")
        return False


def _send_meeting_push(user, meeting):
    """
    Send meeting push notification to a user's mobile devices.
    """
    try:
        # Format meeting info for push notification
        date_str = meeting.scheduled_date.strftime('%b %d')
        time_str = meeting.scheduled_time.strftime('%I:%M %p')
        
        # Determine location for notification
        if meeting.is_virtual:
            location_text = "Virtual"
        elif meeting.is_hybrid:
            location_text = "Hybrid"
        else:
            location_text = meeting.venue[:20] if meeting.venue else "TBA"
        
        title = f"📅 {meeting.get_meeting_type_display()} Meeting"
        body = f"{meeting.title}\n📆 {date_str} at {time_str}\n📍 {location_text}"
        
        # Data payload for deep linking
        data = {
            'type': 'meeting_invitation',
            'meeting_id': str(meeting.meeting_id),
            'screen': 'MeetingDetails',
            'title': meeting.title,
        }
        
        result = PushNotificationService.send_to_user(
            user=user,
            title=title,
            body=body,
            data=data,
            priority='high',
        )
        
        return result.get('success', False)
        
    except Exception as e:
        logger.error(f"Error sending push notification to {user.phone or user.pk}: {str(e)}")
        return False


# Optional: Signal for meeting updates (notify attendees when meeting is rescheduled)
@receiver(post_save, sender=Meeting)
def send_meeting_update_notifications(sender, instance, created, **kwargs):
    """
    Notify attendees when a meeting is updated (rescheduled, cancelled, etc.)
    """
    if created:
        return  # Skip for new meetings (handled by send_meeting_notifications)
    
    # Check if we should notify about the update
    # We use a flag in the instance to prevent notification loops
    if hasattr(instance, '_skip_update_notification') and instance._skip_update_notification:
        return
    
    # Get the previous state from the database
    try:
        old_meeting = Meeting.objects.get(meeting_id=instance.meeting_id)
    except Meeting.DoesNotExist:
        return
    
    # Detect significant changes
    significant_changes = []
    
    # Check for status change to cancelled
    if instance.status == 'cancelled' and old_meeting.status != 'cancelled':
        _send_cancellation_notifications(instance)
        return
    
    # Check for date/time changes (rescheduling)
    if (instance.scheduled_date != old_meeting.scheduled_date or 
        instance.scheduled_time != old_meeting.scheduled_time):
        significant_changes.append('rescheduled')
    
    # Check for venue change
    if instance.venue != old_meeting.venue or instance.virtual_link != old_meeting.virtual_link:
        significant_changes.append('venue_changed')
    
    if significant_changes:
        # Use thread to send update notifications
        thread = threading.Thread(
            target=_send_meeting_update_async,
            args=(instance.meeting_id, significant_changes)
        )
        thread.daemon = True
        thread.start()


def _send_meeting_update_async(meeting_id, changes):
    """Send meeting update notifications asynchronously."""
    from .models import Meeting
    import time
    
    time.sleep(0.5)
    
    try:
        meeting = Meeting.objects.get(meeting_id=meeting_id)
    except Meeting.DoesNotExist:
        return
    
    attendees = meeting.expected_attendees
    
    for user in attendees:
        # Send push notification about the update
        try:
            date_str = meeting.scheduled_date.strftime('%b %d')
            time_str = meeting.scheduled_time.strftime('%I:%M %p')
            
            if 'rescheduled' in changes:
                title = "📅 Meeting Rescheduled"
                body = f"{meeting.title} has been rescheduled to {date_str} at {time_str}"
            else:
                title = "📅 Meeting Updated"
                body = f"{meeting.title} details have been updated. Please check for changes."
            
            PushNotificationService.send_to_user(
                user=user,
                title=title,
                body=body,
                data={
                    'type': 'meeting_update',
                    'meeting_id': str(meeting.meeting_id),
                    'screen': 'MeetingDetails',
                },
                priority='high',
            )
        except Exception as e:
            logger.error(f"Error sending update push to {user.pk}: {e}")


def _send_cancellation_notifications(meeting):
    """Send notifications when a meeting is cancelled."""
    attendees = meeting.expected_attendees
    
    for user in attendees:
        # Send push notification
        try:
            date_str = meeting.scheduled_date.strftime('%b %d')
            
            PushNotificationService.send_to_user(
                user=user,
                title="❌ Meeting Cancelled",
                body=f"{meeting.title} scheduled for {date_str} has been cancelled.",
                data={
                    'type': 'meeting_cancelled',
                    'meeting_id': str(meeting.meeting_id),
                },
                priority='high',
            )
        except Exception as e:
            logger.error(f"Error sending cancellation push to {user.pk}: {e}")
        
        # Send SMS for cancellation
        try:
            phone = getattr(user, 'phone', None)
            if phone:
                phone = str(phone) if phone else None
                if phone:
                    phone = normalize_phone(phone)
                    date_str = meeting.scheduled_date.strftime('%b %d, %Y')
                    context = {
                        'meeting_title': meeting.title[:50],
                        'meeting_date': date_str,
                    }
                    send_sms_message(
                        phone=phone,
                        template='executives/meeting_cancelled_sms.txt',
                        context=context,
                        is_otp=False,
                    )
        except Exception as e:
            logger.error(f"Error sending cancellation SMS to {user.pk}: {e}")
