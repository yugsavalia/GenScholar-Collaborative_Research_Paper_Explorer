from django.apps import AppConfig


class PdfsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pdfs'

    def ready(self):
        import pdfs.signals  # <-- ADD THIS LINE to register the signals