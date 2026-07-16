from django.apps import AppConfig


class ExecutivesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'executives'

    def ready(self):
        # Import signals to register them
        import executives.signals  # noqa: F401
