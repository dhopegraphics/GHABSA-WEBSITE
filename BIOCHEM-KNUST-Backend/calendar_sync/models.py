"""
Calendar Sync Models
Manages calendar tokens for secure subscription access
"""
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from uuid import uuid4
import secrets
import hashlib

User = get_user_model()


def generate_calendar_token():
    """Generate a secure, URL-safe token for calendar subscriptions"""
    return secrets.token_urlsafe(32)


class CalendarToken(models.Model):
    """
    Secure token for calendar subscription access.
    Each user can have multiple tokens for different calendar types.
    """
    CALENDAR_TYPES = (
        ('full', 'Full Academic Calendar'),
        ('classes', 'Class Timetable'),
        ('exams', 'Exam Schedule'),
        ('events', 'Events Calendar'),
        ('personal', 'Personal Combined Calendar'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='calendar_tokens'
    )
    calendar_type = models.CharField(
        max_length=20,
        choices=CALENDAR_TYPES,
        default='personal'
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_calendar_token,
        db_index=True
    )
    name = models.CharField(
        max_length=100,
        blank=True,
        help_text="Optional friendly name for this calendar subscription"
    )
    
    # Access tracking
    is_active = models.BooleanField(default=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    access_count = models.PositiveIntegerField(default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Optional expiration date for this token"
    )
    
    class Meta:
        verbose_name = "Calendar Token"
        verbose_name_plural = "Calendar Tokens"
        unique_together = ['user', 'calendar_type']
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.user.username} - {self.get_calendar_type_display()}"
    
    @property
    def is_valid(self):
        """Check if token is still valid (active and not expired)"""
        if not self.is_active:
            return False
        if self.expires_at and timezone.now() > self.expires_at:
            return False
        return True
    
    def record_access(self):
        """Record that this token was used to access the calendar"""
        self.last_accessed = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_accessed', 'access_count'])
    
    def regenerate_token(self):
        """Generate a new token (invalidates old subscription URLs)"""
        self.token = generate_calendar_token()
        self.save(update_fields=['token', 'updated_at'])
        return self.token
    
    @classmethod
    def get_or_create_for_user(cls, user, calendar_type='personal'):
        """Get existing token or create new one for user and calendar type"""
        token, created = cls.objects.get_or_create(
            user=user,
            calendar_type=calendar_type,
            defaults={'name': f"{user.first_name}'s {dict(cls.CALENDAR_TYPES).get(calendar_type, 'Calendar')}"}
        )
        return token


class CalendarReminderPreference(models.Model):
    """
    User preferences for calendar reminders.
    Allows users to configure when and how often they receive reminders.
    """
    REMINDER_TYPES = (
        ('class', 'Class Reminders'),
        ('exam', 'Exam Reminders'),
        ('event', 'Event Reminders'),
    )
    
    # Default reminder times in minutes before event
    DEFAULT_CLASS_REMINDERS = [15, 30]  # 15 and 30 minutes before
    DEFAULT_EXAM_REMINDERS = [1440, 120, 30]  # 1 day, 2 hours, 30 minutes before
    DEFAULT_EVENT_REMINDERS = [60, 1440]  # 1 hour and 1 day before
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='calendar_reminder_preferences'
    )
    
    # Class reminders (in minutes before)
    class_reminders_enabled = models.BooleanField(default=True)
    class_reminder_times = models.JSONField(
        default=list,
        help_text="List of minutes before class to send reminders. e.g., [15, 30, 60]"
    )
    
    # Exam reminders (in minutes before)
    exam_reminders_enabled = models.BooleanField(default=True)
    exam_reminder_times = models.JSONField(
        default=list,
        help_text="List of minutes before exam to send reminders. e.g., [30, 120, 1440]"
    )
    
    # Event reminders (in minutes before)
    event_reminders_enabled = models.BooleanField(default=True)
    event_reminder_times = models.JSONField(
        default=list,
        help_text="List of minutes before event to send reminders. e.g., [60, 1440]"
    )
    
    # Push notification settings
    push_reminders_enabled = models.BooleanField(
        default=True,
        help_text="Send push notifications as reminders (most reliable)"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Calendar Reminder Preference"
        verbose_name_plural = "Calendar Reminder Preferences"
    
    def __str__(self):
        return f"Reminder Prefs: {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Set default reminder times if not provided
        if not self.class_reminder_times:
            self.class_reminder_times = self.DEFAULT_CLASS_REMINDERS
        if not self.exam_reminder_times:
            self.exam_reminder_times = self.DEFAULT_EXAM_REMINDERS
        if not self.event_reminder_times:
            self.event_reminder_times = self.DEFAULT_EVENT_REMINDERS
        super().save(*args, **kwargs)
    
    def get_reminder_times(self, reminder_type: str) -> list:
        """Get reminder times for a specific type"""
        mapping = {
            'class': (self.class_reminders_enabled, self.class_reminder_times),
            'exam': (self.exam_reminders_enabled, self.exam_reminder_times),
            'event': (self.event_reminders_enabled, self.event_reminder_times),
        }
        enabled, times = mapping.get(reminder_type, (False, []))
        return times if enabled else []
    
    @classmethod
    def get_for_user(cls, user):
        """Get or create reminder preferences for a user"""
        prefs, created = cls.objects.get_or_create(
            user=user,
            defaults={
                'class_reminder_times': cls.DEFAULT_CLASS_REMINDERS,
                'exam_reminder_times': cls.DEFAULT_EXAM_REMINDERS,
                'event_reminder_times': cls.DEFAULT_EVENT_REMINDERS,
            }
        )
        return prefs


class ScheduledCalendarReminder(models.Model):
    """
    Scheduled reminders for calendar events.
    These are processed by a Celery task and sent as push notifications.
    """
    REMINDER_TYPES = (
        ('class', 'Class Reminder'),
        ('exam', 'Exam Reminder'),
        ('event', 'Event Reminder'),
    )
    
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('skipped', 'Skipped'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='calendar_reminders'
    )
    
    reminder_type = models.CharField(max_length=20, choices=REMINDER_TYPES)
    
    # Reference to the actual event
    reference_model = models.CharField(
        max_length=50,
        help_text="Model name e.g., 'ClassSchedule', 'ExaminationSchedule', 'Event'"
    )
    reference_id = models.CharField(
        max_length=100,
        help_text="ID of the referenced object"
    )
    
    # Reminder content
    title = models.CharField(max_length=200)
    message = models.TextField()
    
    # When to send
    event_datetime = models.DateTimeField(help_text="When the actual event starts")
    remind_at = models.DateTimeField(
        db_index=True,
        help_text="When to send this reminder"
    )
    minutes_before = models.PositiveIntegerField(
        help_text="How many minutes before the event this reminder is for"
    )
    
    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    sent_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)
    
    # Prevent duplicates
    unique_key = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique identifier to prevent duplicate reminders"
    )
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Scheduled Calendar Reminder"
        verbose_name_plural = "Scheduled Calendar Reminders"
        ordering = ['remind_at']
        indexes = [
            models.Index(fields=['status', 'remind_at']),
            models.Index(fields=['user', 'status']),
            models.Index(fields=['reminder_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.reminder_type}: {self.title} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Generate unique key if not provided
        if not self.unique_key:
            self.unique_key = f"{self.user_id}-{self.reminder_type}-{self.reference_id}-{self.minutes_before}"
        super().save(*args, **kwargs)
    
    @classmethod
    def schedule_reminder(
        cls,
        user,
        reminder_type: str,
        reference_model: str,
        reference_id: str,
        title: str,
        message: str,
        event_datetime,
        minutes_before: int
    ):
        """Schedule a reminder for a calendar event"""
        from datetime import timedelta
        
        remind_at = event_datetime - timedelta(minutes=minutes_before)
        
        # Don't schedule reminders in the past
        if remind_at <= timezone.now():
            return None
        
        unique_key = f"{user.id}-{reminder_type}-{reference_id}-{minutes_before}"
        
        reminder, created = cls.objects.update_or_create(
            unique_key=unique_key,
            defaults={
                'user': user,
                'reminder_type': reminder_type,
                'reference_model': reference_model,
                'reference_id': reference_id,
                'title': title,
                'message': message,
                'event_datetime': event_datetime,
                'remind_at': remind_at,
                'minutes_before': minutes_before,
                'status': 'pending',
            }
        )
        return reminder


class PublicCalendarToken(models.Model):
    """
    Public calendar tokens for non-authenticated access.
    Used for public events calendar that anyone can subscribe to.
    """
    CALENDAR_TYPES = (
        ('public_events', 'Public Events Calendar'),
        ('academic', 'Academic Calendar (Exams)'),
    )
    
    id = models.UUIDField(primary_key=True, default=uuid4, editable=False)
    calendar_type = models.CharField(
        max_length=20,
        choices=CALENDAR_TYPES,
        unique=True
    )
    token = models.CharField(
        max_length=64,
        unique=True,
        default=generate_calendar_token,
        db_index=True
    )
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    
    is_active = models.BooleanField(default=True)
    last_accessed = models.DateTimeField(null=True, blank=True)
    access_count = models.PositiveIntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Public Calendar Token"
        verbose_name_plural = "Public Calendar Tokens"
    
    def __str__(self):
        return f"Public: {self.name}"
    
    def record_access(self):
        self.last_accessed = timezone.now()
        self.access_count += 1
        self.save(update_fields=['last_accessed', 'access_count'])
