from django.apps import AppConfig
from loguru import logger


class AppMarketConfig(AppConfig):
    name = 'app_market'

    def ready(self):
        import app_market.signals  # Импортируем сигналы

        from app_sockets.models import Socket

        try:
            # Удаляем старые сокеты из бд при запуске сервера
            Socket.objects.all().delete()
        except Exception as e:
            logger.error(e)
