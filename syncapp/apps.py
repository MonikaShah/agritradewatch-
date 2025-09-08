from django.apps import AppConfig
import threading

class SyncappConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'syncapp'

    def ready(self):
        # Import the function from your existing firebase_listener.py
        # from .firebase_listener import fetch_firestore_and_insert

        # # Run Firestore → Postgres sync in a separate thread
        # threading.Thread(target=fetch_firestore_and_insert, daemon=True).start()
        pass