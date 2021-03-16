from django.apps import AppConfig


class AppMarketConfig(AppConfig):
    name = 'app_market'

    def ready(self):
        import app_market.signals  # Импортируем сигналы
