"""
Calendar Sync App Configuration
"""
from django.apps import AppConfig


class CalendarSyncConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'calendar_sync'
    verbose_name = 'Calendar Synchronization'
    
    def ready(self):
        """Run when app is ready - import signals"""
        import calendar_sync.signals  # noqa
