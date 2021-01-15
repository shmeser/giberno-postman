from django.urls import path

from app_market.views import Vacancies, Professions, suggest_profession

urlpatterns = [
    path('market/vacancies', Vacancies.as_view()),
    path('market/professions', Professions.as_view()),
    path('market/professions/suggest', suggest_profession),
]
