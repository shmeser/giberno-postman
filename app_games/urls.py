from django.urls import path

from app_games.views import Prizes, LikePrize, PrizesDocuments, PrizeCards, Tasks, bonus_progress_for_prizes

urlpatterns = [

    # Призы
    path('games/prizes', Prizes.as_view()),
    path('games/prizes/<int:record_id>', Prizes.as_view()),

    path('games/prizes/<int:record_id>/like', LikePrize.as_view()),

    path('games/prizes/documents', PrizesDocuments.as_view()),
    path('games/prizes/progress', bonus_progress_for_prizes),

    # Призовые карточки
    path('games/cards', PrizeCards.as_view()),

    # Задания
    path('games/tasks', Tasks.as_view()),
]
