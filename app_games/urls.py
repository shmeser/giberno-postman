from django.urls import path

from app_games.views import Prizes, LikePrize, PrizesDocuments, PrizeCards, Tasks

urlpatterns = [

    # Призы
    path('games/prizes', Prizes.as_view()),
    path('games/prizes/<int:record_id>', Prizes.as_view()),

    path('games/prizes/<int:record_id>/like', LikePrize.as_view()),

    path('games/prizes/documents', PrizesDocuments.as_view()),

    # Призовые карточки
    path('games/cards', PrizeCards.as_view()),

    # Задания
    path('games/tasks', Tasks.as_view()),
]
