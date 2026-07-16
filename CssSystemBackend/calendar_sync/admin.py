"""
Calendar Sync Admin Configuration
"""
from django.contrib import admin
from .models import (
    CalendarToken,
    PublicCalendarToken,
    CalendarReminderPreference,
    ScheduledCalendarReminder
)


@admin.register(CalendarToken)
class CalendarTokenAdmin(admin.ModelAdmin):
    """Admin for user calendar tokens"""
    list_display = [
        'user',
        'name',
        'calendar_type',
        'is_active',
        'is_valid_display',
        'access_count',
        'last_accessed',
        'created_at',
    ]
    list_filter = [
        'calendar_type',
        'is_active',
        'created_at',
    ]
    search_fields = [
        'user__username',
        'user__personal_email',
        'user__student_email',
        'name',
        'token',
    ]
    readonly_fields = [
        'token',
        'created_at',
        'updated_at',
        'last_accessed',
        'access_count',
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('user', 'name', 'calendar_type')
        }),
        ('Token Info', {
            'fields': ('token', 'is_active', 'expires_at')
        }),
        ('Usage Stats', {
            'fields': ('last_accessed', 'access_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def is_valid_display(self, obj):
        """Display token validity"""
        return obj.is_valid
    is_valid_display.short_description = 'Valid'
    is_valid_display.boolean = True
    
    actions = ['regenerate_tokens', 'deactivate_tokens', 'activate_tokens']
    
    @admin.action(description='Regenerate selected tokens')
    def regenerate_tokens(self, request, queryset):
        for token in queryset:
            token.regenerate_token()
        self.message_user(request, f'Regenerated {queryset.count()} tokens')
    
    @admin.action(description='Deactivate selected tokens')
    def deactivate_tokens(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {queryset.count()} tokens')
    
    @admin.action(description='Activate selected tokens')
    def activate_tokens(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'Activated {queryset.count()} tokens')


@admin.register(PublicCalendarToken)
class PublicCalendarTokenAdmin(admin.ModelAdmin):
    """Admin for public calendar tokens"""
    list_display = [
        'name',
        'calendar_type',
        'token_preview',
        'is_active',
        'access_count',
        'last_accessed',
        'created_at',
    ]
    list_filter = [
        'calendar_type',
        'is_active',
        'created_at',
    ]
    search_fields = [
        'name',
        'token',
    ]
    readonly_fields = [
        'token',
        'created_at',
        'updated_at',
        'last_accessed',
        'access_count',
    ]
    ordering = ['-created_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'calendar_type', 'description')
        }),
        ('Token Info', {
            'fields': ('token', 'is_active')
        }),
        ('Usage Stats', {
            'fields': ('last_accessed', 'access_count')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def token_preview(self, obj):
        """Show truncated token"""
        return f"{obj.token[:8]}..."
    token_preview.short_description = 'Token'
    
    actions = ['regenerate_tokens', 'deactivate_tokens', 'activate_tokens']
    
    @admin.action(description='Regenerate selected tokens')
    def regenerate_tokens(self, request, queryset):
        for token in queryset:
            token.regenerate_token()
        self.message_user(request, f'Regenerated {queryset.count()} tokens')
    
    @admin.action(description='Deactivate selected tokens')
    def deactivate_tokens(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'Deactivated {queryset.count()} tokens')
    
    @admin.action(description='Activate selected tokens')
    def activate_tokens(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'Activated {queryset.count()} tokens')


@admin.register(CalendarReminderPreference)
class CalendarReminderPreferenceAdmin(admin.ModelAdmin):
    """Admin for calendar reminder preferences"""
    list_display = [
        'user',
        'class_reminders_enabled',
        'exam_reminders_enabled',
        'event_reminders_enabled',
        'push_reminders_enabled',
        'updated_at',
    ]
    list_filter = [
        'class_reminders_enabled',
        'exam_reminders_enabled',
        'event_reminders_enabled',
        'push_reminders_enabled',
    ]
    search_fields = [
        'user__username',
        'user__personal_email',
        'user__student_email',
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('user',)
        }),
        ('Class Reminders', {
            'fields': ('class_reminders_enabled', 'class_reminder_times'),
            'description': 'Times are in minutes before the class (e.g., [15, 30] = 15 and 30 mins before)'
        }),
        ('Exam Reminders', {
            'fields': ('exam_reminders_enabled', 'exam_reminder_times'),
            'description': 'Times are in minutes (e.g., [1440, 120, 30] = 1 day, 2 hours, 30 mins before)'
        }),
        ('Event Reminders', {
            'fields': ('event_reminders_enabled', 'event_reminder_times'),
        }),
        ('Push Notifications', {
            'fields': ('push_reminders_enabled',),
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ScheduledCalendarReminder)
class ScheduledCalendarReminderAdmin(admin.ModelAdmin):
    """Admin for scheduled calendar reminders"""
    list_display = [
        'user',
        'reminder_type',
        'title_preview',
        'minutes_before',
        'remind_at',
        'event_datetime',
        'status',
        'sent_at',
    ]
    list_filter = [
        'reminder_type',
        'status',
        'remind_at',
        'created_at',
    ]
    search_fields = [
        'user__username',
        'title',
        'message',
        'reference_id',
    ]
    readonly_fields = [
        'unique_key',
        'sent_at',
        'created_at',
        'updated_at',
    ]
    ordering = ['-remind_at']
    date_hierarchy = 'remind_at'
    
    fieldsets = (
        (None, {
            'fields': ('user', 'reminder_type', 'status')
        }),
        ('Content', {
            'fields': ('title', 'message')
        }),
        ('Schedule', {
            'fields': ('event_datetime', 'remind_at', 'minutes_before')
        }),
        ('Reference', {
            'fields': ('reference_model', 'reference_id', 'unique_key')
        }),
        ('Status', {
            'fields': ('sent_at', 'error_message'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def title_preview(self, obj):
        return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
    title_preview.short_description = 'Title'
    
    actions = ['mark_as_sent', 'mark_as_pending', 'cancel_reminders']
    
    @admin.action(description='Mark selected as sent')
    def mark_as_sent(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='sent', sent_at=timezone.now())
        self.message_user(request, f'Marked {queryset.count()} reminders as sent')
    
    @admin.action(description='Mark selected as pending')
    def mark_as_pending(self, request, queryset):
        queryset.update(status='pending', sent_at=None)
        self.message_user(request, f'Marked {queryset.count()} reminders as pending')
    
    @admin.action(description='Cancel selected reminders')
    def cancel_reminders(self, request, queryset):
        queryset.update(status='skipped')
        self.message_user(request, f'Cancelled {queryset.count()} reminders')
