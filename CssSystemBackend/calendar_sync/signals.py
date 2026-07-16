"""
Calendar Sync Signals
Handles automatic actions when calendar-related models change.
"""
from django.db.models.signals import post_save
from django.dispatch import receiver
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender='calendar_sync.CalendarToken')
def on_calendar_token_created(sender, instance, created, **kwargs):
    """
    When a user creates their first calendar token, sync their reminders.
    This ensures they start receiving push notifications right away.
    """
    if created and instance.is_active:
        # Check if this is the user's first token
        from .models import CalendarToken
        token_count = CalendarToken.objects.filter(
            user=instance.user,
            is_active=True
        ).count()
        
        # Only sync on first token creation
        if token_count == 1:
            logger.info(f"First calendar token created for user {instance.user.id}, scheduling reminder sync")
            
            # Trigger async reminder sync
            try:
                from .tasks import sync_user_reminders
                sync_user_reminders.delay(str(instance.user.id))
            except Exception as e:
                logger.error(f"Failed to trigger reminder sync for user {instance.user.id}: {e}")


@receiver(post_save, sender='calendar_sync.CalendarReminderPreference')
def on_reminder_preferences_changed(sender, instance, created, **kwargs):
    """
    When a user updates their reminder preferences, re-sync their reminders.
    """
    if not created:  # Only on update, not create
        logger.info(f"Reminder preferences updated for user {instance.user.id}, scheduling reminder sync")
        
        try:
            from .tasks import sync_user_reminders
            sync_user_reminders.delay(str(instance.user.id))
        except Exception as e:
            logger.error(f"Failed to trigger reminder sync for user {instance.user.id}: {e}")
