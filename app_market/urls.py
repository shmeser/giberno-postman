from django.urls import path

from app_market.views import Vacancies, Professions, suggest_profession, Skills, Distributors, Shops

urlpatterns = [
    path('market/distributors', Distributors.as_view()),
    path('market/distributors/<int:record_id>', Distributors.as_view()),

    path('market/shops', Shops.as_view()),
    path('market/shops/<int:record_id>', Shops.as_view()),

    path('market/vacancies', Vacancies.as_view()),
    path('market/vacancies/<int:record_id>', Vacancies.as_view()),

    path('market/professions', Professions.as_view()),
    path('market/professions/suggest', suggest_profession),

    path('market/skills', Skills.as_view()),
]
