from django.apps import AppConfig


class ElMercadoConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'el_mercado'
    
    def ready(self):
        """Import signal handlers when app is ready"""
        import el_mercado.signals  # noqa
