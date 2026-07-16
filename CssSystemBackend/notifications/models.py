from django.db import models
from django.utils import timezone
from accounts.models import CustomUser
from uuid import uuid4
import json


class PushNotificationDevice(models.Model):
    """Store user device tokens for push notifications"""
    
    PLATFORM_CHOICES = [
        ('ios', 'iOS'),
        ('android', 'Android'),
        ('web', 'Web'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='push_devices')
    device_token = models.TextField(unique=True, help_text="Expo push token or FCM token")
    platform = models.CharField(max_length=10, choices=PLATFORM_CHOICES)
    device_name = models.CharField(max_length=255, blank=True, null=True, help_text="Device name or model")
    
    # Web Push specific fields (for browser notifications)
    web_subscription = models.JSONField(
        null=True,
        blank=True,
        help_text="Web Push subscription object containing endpoint, keys (p256dh, auth)"
    )
    
    is_active = models.BooleanField(default=True, help_text="Whether this device should receive notifications")
    last_used = models.DateTimeField(auto_now=True)
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'push_notification_devices'
        verbose_name = 'Push Notification Device'
        verbose_name_plural = 'Push Notification Devices'
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['device_token']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.platform} ({self.device_token[:20]}...)"


class PushNotificationTemplate(models.Model):
    """Reusable templates for different types of notifications"""
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100, unique=True, help_text="Template identifier (e.g., 'class_reminder')")
    title = models.CharField(max_length=100, help_text="Notification title (supports {variable} placeholders)")
    body = models.TextField(help_text="Notification body (supports {variable} placeholders)")
    data = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional data payload as JSON (e.g., {'screen': 'ClassSchedule', 'scheduleId': '{schedule_id}'})"
    )
    sound = models.CharField(max_length=50, default='default', help_text="Notification sound")
    priority = models.CharField(
        max_length=10,
        choices=[('high', 'High'), ('default', 'Default'), ('low', 'Low')],
        default='default'
    )
    badge = models.IntegerField(default=1, help_text="Badge count for iOS")
    category = models.CharField(max_length=50, blank=True, null=True, help_text="Notification category")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'push_notification_templates'
        verbose_name = 'Push Notification Template'
        verbose_name_plural = 'Push Notification Templates'
    
    def __str__(self):
        return self.name
    
    def render(self, context):
        """Render template with context variables"""
        title = self.title.format(**context)
        body = self.body.format(**context)
        data = {}
        
        # Render data payload
        if self.data:
            data_str = json.dumps(self.data)
            data_str = data_str.format(**context)
            data = json.loads(data_str)
        
        return {
            'title': title,
            'body': body,
            'data': data,
            'sound': self.sound,
            'priority': self.priority,
            'badge': self.badge,
            'category': self.category,
        }


class PushNotification(models.Model):
    """Individual push notification records"""
    
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('scheduled', 'Scheduled'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='push_notifications')
    template = models.ForeignKey(
        PushNotificationTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        help_text="Template used (optional)"
    )
    title = models.CharField(max_length=100)
    body = models.TextField()
    data = models.JSONField(default=dict, blank=True, help_text="Additional data payload")
    sound = models.CharField(max_length=50, default='default')
    priority = models.CharField(max_length=10, default='default')
    badge = models.IntegerField(default=1)
    category = models.CharField(max_length=50, blank=True, null=True)
    
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    scheduled_at = models.DateTimeField(null=True, blank=True, help_text="When to send this notification")
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True, null=True)
    
    # Track what triggered this notification
    trigger_type = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="e.g., 'class_schedule', 'exam_schedule', 'manual'"
    )
    trigger_id = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="ID of the object that triggered this notification"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'push_notifications'
        verbose_name = 'Push Notification'
        verbose_name_plural = 'Push Notifications'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['scheduled_at', 'status']),
            models.Index(fields=['trigger_type', 'trigger_id']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.title} ({self.status})"


class NotificationTrigger(models.Model):
    """Define automatic notification triggers based on conditions"""
    
    TRIGGER_TYPE_CHOICES = [
        ('class_schedule', 'Class Schedule'),
        ('exam_schedule', 'Exam Schedule'),
        ('event', 'Event'),
        ('deadline', 'Deadline'),
        ('custom', 'Custom'),
    ]
    
    TIME_UNIT_CHOICES = [
        ('minutes', 'Minutes'),
        ('hours', 'Hours'),
        ('days', 'Days'),
        ('weeks', 'Weeks'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    name = models.CharField(max_length=100, help_text="Descriptive name for this trigger")
    trigger_type = models.CharField(max_length=50, choices=TRIGGER_TYPE_CHOICES)
    template = models.ForeignKey(PushNotificationTemplate, on_delete=models.CASCADE)
    
    # Time offset configuration
    offset_value = models.IntegerField(help_text="Time before event (e.g., 1, 24)")
    offset_unit = models.CharField(max_length=10, choices=TIME_UNIT_CHOICES, default='hours')
    
    # Conditions (stored as JSON for flexibility)
    conditions = models.JSONField(
        default=dict,
        blank=True,
        help_text="Additional conditions (e.g., {'day_of_week': [1,2,3], 'program': 'CS'})"
    )
    
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_triggers'
        verbose_name = 'Notification Trigger'
        verbose_name_plural = 'Notification Triggers'
    
    def __str__(self):
        return f"{self.name} - {self.offset_value} {self.offset_unit} before"
    
    def calculate_notification_time(self, event_time):
        """Calculate when to send notification based on offset"""
        from datetime import timedelta
        
        offset_map = {
            'minutes': timedelta(minutes=self.offset_value),
            'hours': timedelta(hours=self.offset_value),
            'days': timedelta(days=self.offset_value),
            'weeks': timedelta(weeks=self.offset_value),
        }
        
        return event_time - offset_map[self.offset_unit]


class NotificationPreference(models.Model):
    """User preferences for notifications"""
    
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='notification_preferences')
    
    # Global settings
    push_enabled = models.BooleanField(default=True)
    sms_enabled = models.BooleanField(default=True)
    email_enabled = models.BooleanField(default=True)
    
    # Category-specific settings
    class_reminders = models.BooleanField(default=True)
    exam_reminders = models.BooleanField(default=True)
    event_notifications = models.BooleanField(default=True)
    deadline_reminders = models.BooleanField(default=True)
    general_announcements = models.BooleanField(default=True)
    
    # Quiet hours
    quiet_hours_enabled = models.BooleanField(default=False)
    quiet_hours_start = models.TimeField(null=True, blank=True, help_text="e.g., 22:00")
    quiet_hours_end = models.TimeField(null=True, blank=True, help_text="e.g., 07:00")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        db_table = 'notification_preferences'
        verbose_name = 'Notification Preference'
        verbose_name_plural = 'Notification Preferences'
    
    def __str__(self):
        return f"Preferences for {self.user.username}"
    
    def is_in_quiet_hours(self):
        """Check if current time is within quiet hours"""
        if not self.quiet_hours_enabled or not self.quiet_hours_start or not self.quiet_hours_end:
            return False
        
        now = timezone.localtime().time()
        start = self.quiet_hours_start
        end = self.quiet_hours_end
        
        if start <= end:
            return start <= now <= end
        else:  # Quiet hours span midnight
            return now >= start or now <= end


class RecentUpdateReadStatus(models.Model):
    """
    Track which recent updates/notifications a user has read
    Used to show unread counts and filter notifications
    """
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='read_updates')
    update_id = models.CharField(
        max_length=255,
        help_text="The ID of the update (e.g., 'event-{uuid}', 'helpdesk-{tracking_id}')"
    )
    update_type = models.CharField(
        max_length=50,
        help_text="Type of update (task_created, event_created, etc.)"
    )
    read_at = models.DateTimeField(auto_now_add=True)
    is_deleted = models.BooleanField(default=False, help_text="User deleted this notification")
    deleted_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        db_table = 'recent_update_read_status'
        verbose_name = 'Recent Update Read Status'
        verbose_name_plural = 'Recent Update Read Statuses'
        unique_together = ('user', 'update_id')
        indexes = [
            models.Index(fields=['user', 'is_deleted']),
            models.Index(fields=['update_id']),
            models.Index(fields=['read_at']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.update_id} ({'deleted' if self.is_deleted else 'read'})"
