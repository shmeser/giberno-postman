from django.urls import path

from app_games import views
urlpatterns = [

    # Призы
    path('games/prizes', views.Prizes.as_view()),
    path('games/prizes/<int:record_id>', views.Prizes.as_view()),

    path('games/prizes/<int:record_id>/like', views.LikePrize.as_view()),

    path('games/prizes/documents', views.PrizesDocuments.as_view()),
    path('games/prizes/progress', views.bonus_progress_for_prizes),

    # Призовые карточки
    path('games/cards', views.PrizeCards.as_view()),
    path('games/cards/<int:record_id>/open', views.OpenPrizeCard.as_view()),

    # Задания
    path('games/tasks', views.Tasks.as_view()),
    path('games/tasks/count', views.TasksCount.as_view()),
    path('games/tasks/<int:record_id>', views.Tasks.as_view()),
]

admin_panel = [
    path('admin/games/tasks', views.AdminTasks.as_view()),
    path('admin/games/tasks/<int:record_id>', views.AdminTask.as_view()),
    path('admin/games/prizes', views.AdminPrizes.as_view()),
    path('admin/games/prizes/<int:record_id>', views.AdminPrize.as_view()),
    path('admin/games/bonuses', views.AdminUsersBonuses.as_view()),
    path('admin/games/bonuses/<int:record_id>', views.AdminUserBonuses.as_view()),
]

urlpatterns += admin_panel
