"""
Calendar Sync Serializers
"""
from rest_framework import serializers
from .models import CalendarToken, PublicCalendarToken


class CalendarTokenSerializer(serializers.ModelSerializer):
    """Serializer for CalendarToken"""
    subscription_url = serializers.SerializerMethodField()
    webcal_url = serializers.SerializerMethodField()
    download_url = serializers.SerializerMethodField()
    calendar_type_display = serializers.CharField(
        source='get_calendar_type_display', 
        read_only=True
    )
    
    class Meta:
        model = CalendarToken
        fields = [
            'id',
            'name',
            'calendar_type',
            'calendar_type_display',
            'token',
            'is_active',
            'is_valid',
            'expires_at',
            'last_accessed',
            'access_count',
            'subscription_url',
            'webcal_url',
            'download_url',
            'created_at',
        ]
        read_only_fields = [
            'id',
            'token',
            'is_active',
            'is_valid',
            'expires_at',
            'last_accessed',
            'access_count',
            'created_at',
        ]
    
    def get_subscription_url(self, obj):
        """Get HTTP subscription URL"""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/calendar/subscribe/{obj.token}/')
        return f'/calendar/subscribe/{obj.token}/'
    
    def get_webcal_url(self, obj):
        """Get webcal:// URL for iOS/macOS"""
        request = self.context.get('request')
        if request:
            url = request.build_absolute_uri(f'/calendar/subscribe/{obj.token}/')
            return url.replace('http://', 'webcal://').replace('https://', 'webcal://')
        return f'webcal://your-domain/calendar/subscribe/{obj.token}/'
    
    def get_download_url(self, obj):
        """Get download URL"""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/calendar/download/{obj.calendar_type}/')
        return f'/calendar/download/{obj.calendar_type}/'


class CalendarTokenCreateSerializer(serializers.Serializer):
    """Serializer for creating calendar tokens"""
    calendar_type = serializers.ChoiceField(
        choices=CalendarToken.CALENDAR_TYPES,
        default='personal'
    )
    name = serializers.CharField(max_length=100, required=False, allow_blank=True)


class PublicCalendarTokenSerializer(serializers.ModelSerializer):
    """Serializer for PublicCalendarToken"""
    subscription_url = serializers.SerializerMethodField()
    calendar_type_display = serializers.CharField(
        source='get_calendar_type_display',
        read_only=True
    )
    
    class Meta:
        model = PublicCalendarToken
        fields = [
            'id',
            'name',
            'calendar_type',
            'calendar_type_display',
            'token',
            'is_active',
            'last_accessed',
            'access_count',
            'subscription_url',
            'created_at',
        ]
    
    def get_subscription_url(self, obj):
        """Get subscription URL"""
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(f'/calendar/subscribe/{obj.token}/')
        return f'/calendar/subscribe/{obj.token}/'


class CalendarSubscriptionURLSerializer(serializers.Serializer):
    """Serializer for subscription URL response"""
    name = serializers.CharField()
    http_url = serializers.URLField()
    webcal_url = serializers.CharField()
    download_url = serializers.URLField()


class CalendarExportInfoSerializer(serializers.Serializer):
    """Serializer for calendar export info"""
    calendar_types = serializers.ListField(child=serializers.CharField())
    instructions = serializers.DictField()


class CalendarReminderPreferenceSerializer(serializers.Serializer):
    """Serializer for calendar reminder preferences"""
    from .models import CalendarReminderPreference
    
    # Predefined reminder time options (in minutes)
    REMINDER_TIME_CHOICES = [
        (5, '5 minutes before'),
        (10, '10 minutes before'),
        (15, '15 minutes before'),
        (30, '30 minutes before'),
        (60, '1 hour before'),
        (120, '2 hours before'),
        (180, '3 hours before'),
        (360, '6 hours before'),
        (720, '12 hours before'),
        (1440, '1 day before'),
        (2880, '2 days before'),
        (4320, '3 days before'),
        (10080, '1 week before'),
    ]
    
    id = serializers.UUIDField(read_only=True)
    
    # Class reminders
    class_reminders_enabled = serializers.BooleanField(default=True)
    class_reminder_times = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=10080),
        help_text="List of minutes before class to remind (e.g., [15, 30])"
    )
    
    # Exam reminders
    exam_reminders_enabled = serializers.BooleanField(default=True)
    exam_reminder_times = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=10080),
        help_text="List of minutes before exam to remind (e.g., [30, 120, 1440])"
    )
    
    # Event reminders
    event_reminders_enabled = serializers.BooleanField(default=True)
    event_reminder_times = serializers.ListField(
        child=serializers.IntegerField(min_value=1, max_value=10080),
        help_text="List of minutes before event to remind (e.g., [60, 1440])"
    )
    
    # Push notifications
    push_reminders_enabled = serializers.BooleanField(default=True)
    
    # Timestamps
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    # Include available options for frontend
    available_reminder_times = serializers.SerializerMethodField()
    
    def get_available_reminder_times(self, obj):
        """Return available reminder time options"""
        return [
            {'minutes': minutes, 'label': label}
            for minutes, label in self.REMINDER_TIME_CHOICES
        ]
    
    def validate_class_reminder_times(self, value):
        """Validate class reminder times"""
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 reminder times allowed")
        return sorted(list(set(value)))  # Remove duplicates and sort
    
    def validate_exam_reminder_times(self, value):
        """Validate exam reminder times"""
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 reminder times allowed")
        return sorted(list(set(value)))
    
    def validate_event_reminder_times(self, value):
        """Validate event reminder times"""
        if len(value) > 10:
            raise serializers.ValidationError("Maximum 10 reminder times allowed")
        return sorted(list(set(value)))


class ScheduledReminderSerializer(serializers.Serializer):
    """Serializer for scheduled calendar reminders"""
    id = serializers.UUIDField(read_only=True)
    reminder_type = serializers.CharField()
    title = serializers.CharField()
    message = serializers.CharField()
    event_datetime = serializers.DateTimeField()
    remind_at = serializers.DateTimeField()
    minutes_before = serializers.IntegerField()
    status = serializers.CharField()
    
    # Human-readable time
    time_until = serializers.SerializerMethodField()
    
    def get_time_until(self, obj):
        """Get human-readable time until reminder"""
        from django.utils import timezone
        from datetime import timedelta
        
        now = timezone.now()
        diff = obj.remind_at - now
        
        if diff.total_seconds() < 0:
            return "Past due"
        
        if diff.days > 0:
            return f"In {diff.days} day{'s' if diff.days > 1 else ''}"
        
        hours = diff.seconds // 3600
        minutes = (diff.seconds % 3600) // 60
        
        if hours > 0:
            return f"In {hours}h {minutes}m"
        return f"In {minutes} minutes"

