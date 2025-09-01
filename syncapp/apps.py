from django.apps import AppConfig
import threading

class SyncappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'syncapp'

    def ready(self):
        from .firebase_listener import start_listeners
        threading.Thread(target=start_listeners, daemon=True).start()
