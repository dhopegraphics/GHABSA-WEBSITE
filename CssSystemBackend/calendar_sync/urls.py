"""
Calendar Sync URL Configuration
"""
from django.urls import path
from .views import (
    CalendarTokenListView,
    CalendarTokenDetailView,
    CalendarTokenRegenerateView,
    CalendarSubscriptionURLsView,
    CalendarDownloadView,
    CalendarSubscribeView,
    PublicEventsCalendarView,
    AddSingleEventToCalendarView,
    AddSingleExamToCalendarView,
    CalendarReminderPreferencesView,
    ScheduledRemindersView,
    SyncRemindersView,
)

app_name = 'calendar_sync'

urlpatterns = [
    # Token Management
    path('tokens/', CalendarTokenListView.as_view(), name='token-list'),
    path('tokens/<int:token_id>/', CalendarTokenDetailView.as_view(), name='token-detail'),
    path('tokens/<int:token_id>/regenerate/', CalendarTokenRegenerateView.as_view(), name='token-regenerate'),
    
    # Get Subscription URLs
    path('subscription-urls/', CalendarSubscriptionURLsView.as_view(), name='subscription-urls'),
    
    # Download Calendars (requires auth)
    path('download/<str:calendar_type>/', CalendarDownloadView.as_view(), name='download'),
    
    # Subscribe (token-based auth)
    path('subscribe/<str:token>/', CalendarSubscribeView.as_view(), name='subscribe'),
    
    # Public Calendars
    path('public/events/', PublicEventsCalendarView.as_view(), name='public-events'),
    
    # Single Item Export
    path('event/<str:event_id>/', AddSingleEventToCalendarView.as_view(), name='single-event'),
    path('exam/<int:exam_id>/', AddSingleExamToCalendarView.as_view(), name='single-exam'),
    
    # Reminder Preferences (Push Notifications)
    path('reminder-preferences/', CalendarReminderPreferencesView.as_view(), name='reminder-preferences'),
    path('scheduled-reminders/', ScheduledRemindersView.as_view(), name='scheduled-reminders'),
    path('sync-reminders/', SyncRemindersView.as_view(), name='sync-reminders'),
]
