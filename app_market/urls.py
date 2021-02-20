from django.urls import path

from app_market.views import Vacancies, Professions, suggest_profession, Skills, Distributors, Shops, VacanciesStats, \
    vacancies_suggestions, Shifts, CheckUserShiftByManagerOrSecurityAPIView, ToggleLikeVacancy, \
    ReviewVacancy

urlpatterns = [
    path('market/distributors', Distributors.as_view()),
    path('market/distributors/<int:record_id>', Distributors.as_view()),

    path('market/shops', Shops.as_view()),
    path('market/shops/<int:record_id>', Shops.as_view()),

    path('market/vacancies', Vacancies.as_view()),
    path('market/vacancies/<int:record_id>', Vacancies.as_view()),
    path('market/vacancies/<int:record_id>/reviews', ReviewVacancy.as_view()),
    path('market/vacancies/<int:record_id>/reviews', ReviewVacancy.as_view()),
    path('market/vacancies/<int:record_id>/toggle_like', ToggleLikeVacancy.as_view()),

    path('market/vacancies/stats', VacanciesStats.as_view()),
    path('market/vacancies/suggestions', vacancies_suggestions),

    path('market/shifts', Shifts.as_view()),
    path('market/shifts/<int:record_id>', Shifts.as_view()),
    path('market/shifts/check', CheckUserShiftByManagerOrSecurityAPIView.as_view()),

    path('market/professions', Professions.as_view()),
    path('market/professions/suggest', suggest_profession),

    path('market/skills', Skills.as_view()),
]
