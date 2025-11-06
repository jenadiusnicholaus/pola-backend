from django.apps import AppConfig


class HubsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'hubs'
    
    def ready(self):
        """Import signals when the app is ready"""
        import hubs.signals
