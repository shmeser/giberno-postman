from django.urls import path

from app_market.views import Vacancies, Professions, suggest_profession, Skills

urlpatterns = [
    path('market/vacancies', Vacancies.as_view()),
    path('market/vacancies/<int:record_id>', Vacancies.as_view()),
    path('market/professions', Professions.as_view()),
    path('market/professions/suggest', suggest_profession),
    path('market/skills', Skills.as_view()),
]
