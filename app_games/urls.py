from django.urls import path

from app_games.views import Prizes, LikePrize, PrizesDocuments, PrizeCards, Tasks, bonus_progress_for_prizes, \
    TasksCount, OpenPrizeCard, AdminTasks, AdminPrizes, AdminUsersBonuses, AdminPrize

urlpatterns = [

    # Призы
    path('games/prizes', Prizes.as_view()),
    path('games/prizes/<int:record_id>', Prizes.as_view()),

    path('games/prizes/<int:record_id>/like', LikePrize.as_view()),

    path('games/prizes/documents', PrizesDocuments.as_view()),
    path('games/prizes/progress', bonus_progress_for_prizes),

    # Призовые карточки
    path('games/cards', PrizeCards.as_view()),
    path('games/cards/<int:record_id>/open', OpenPrizeCard.as_view()),

    # Задания
    path('games/tasks', Tasks.as_view()),
    path('games/tasks/count', TasksCount.as_view()),
    path('games/tasks/<int:record_id>', Tasks.as_view()),
]

admin_panel = [
    path('admin/games/tasks', AdminTasks.as_view()),
    path('admin/games/prizes', AdminPrizes.as_view()),
    path('admin/games/prizes/<int:record_id>', AdminPrize.as_view()),
    path('admin/games/bonuses', AdminUsersBonuses.as_view()),
]

urlpatterns += admin_panel
