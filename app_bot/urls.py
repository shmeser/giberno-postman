from django.urls import path
from django.views.decorators.csrf import csrf_exempt

from app_bot.views import TelegramBotView, TestView

urlpatterns = [
    # Чтобы получать запросы от телеграма, в которые нельзя передать CSRF токен, необходимо использовать csrf_exempt
    path('telegram/webhooks', csrf_exempt(TelegramBotView.as_view())),
    path('telegram/webhooks/test', TestView.as_view()),
]
