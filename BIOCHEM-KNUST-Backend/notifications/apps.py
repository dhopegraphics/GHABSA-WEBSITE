from django.apps import AppConfig


class NotificationsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'notifications'
    verbose_name = 'Notifications & Push Notification System'
    
    def ready(self):
        """
        Import signal handlers when Django starts
        This ensures signals are connected when app is ready
        """
        import notifications.signals  # noqa
