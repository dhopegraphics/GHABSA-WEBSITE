from django.apps import AppConfig


class CodequestConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'codequest'
    verbose_name = 'Code Quest Management System'
    
    def ready(self):
        """
        Import signals when the app is ready.
        This ensures signals are connected when Django starts.
        """
        import codequest.signals  # noqa: F401
