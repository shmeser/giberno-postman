from django.urls import path

from app_games.views import Prizes

urlpatterns = [
    path('games/prizes', Prizes.as_view()),
]
