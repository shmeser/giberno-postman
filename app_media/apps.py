from django.apps import AppConfig


class AppMediaConfig(AppConfig):
    name = 'app_media'

    def ready(self):
        import app_media.signals
