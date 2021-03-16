from django.apps import AppConfig
from loguru import logger


class AppSocketsConfig(AppConfig):
    name = 'app_sockets'

    def ready(self):
        from app_sockets.models import Socket

        try:
            # Удаляем старые сокеты из бд при запуске сервера
            Socket.objects.all().delete()
        except Exception as e:
            logger.error(e)
