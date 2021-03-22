from django.urls import path

from app_market.views import Vacancies, Professions, suggest_profession, Skills, Distributors, Shops, VacanciesStats, \
    vacancies_suggestions, Shifts, CheckUserShiftByManagerOrSecurityAPIView, similar_vacancies, ToggleLikeVacancy, \
    VacancyReviewsAPIView, ShopReviewsAPIView, DistributorReviewsAPIView, VacanciesClusteredMap, \
    GetVacanciesByManagerShopAPIView, GetSingleVacancyForManagerAPIView, ApplyToShiftAPIView, UserShiftsListAPIView, \
    GetVacancyAppealsForManagerAPIView, SelfEmployedUserReviewsByAdminOrManagerAPIView, \
    ConfirmAppealByManagerAPIView, RejectAppealByManagerAPIView, UserShiftsRetrieveAPIView, \
    GetVacanciesAvailableDatesForManager

urlpatterns = [
    path('market/distributors', Distributors.as_view()),
    path('market/distributors/<int:record_id>', Distributors.as_view()),
    path('market/distributors/<int:record_id>/reviews', DistributorReviewsAPIView.as_view()),

    path('market/shops', Shops.as_view()),
    path('market/shops/<int:record_id>', Shops.as_view()),
    path('market/shops/<int:record_id>/reviews', ShopReviewsAPIView.as_view()),

    path('market/vacancies', Vacancies.as_view()),
    path('market/vacancies/map', VacanciesClusteredMap.as_view()),
    path('market/vacancies/<int:record_id>', Vacancies.as_view()),
    path('market/vacancies/<int:record_id>/similar', similar_vacancies),
    path('market/vacancies/<int:record_id>/reviews', VacancyReviewsAPIView.as_view()),
    path('market/vacancies/<int:record_id>/toggle_like', ToggleLikeVacancy.as_view()),
    path('market/shifts/<int:record_id>/apply', ApplyToShiftAPIView.as_view()),

    path('market/vacancies/stats', VacanciesStats.as_view()),
    path('market/vacancies/suggestions', vacancies_suggestions),

    path('market/managers/self_employed/<int:record_id>/reviews',
         SelfEmployedUserReviewsByAdminOrManagerAPIView.as_view()),

    path('market/managers/vacancies', GetVacanciesByManagerShopAPIView.as_view()),
    path('market/managers/vacancies/<int:record_id>', GetSingleVacancyForManagerAPIView.as_view()),
    path('market/managers/vacancies/<int:record_id>/appeals',
         GetVacancyAppealsForManagerAPIView.as_view()),
    path('market/managers/vacancies/appeals/<int:record_id>/confirm', ConfirmAppealByManagerAPIView.as_view()),
    path('market/managers/vacancies/appeals/<int:record_id>/reject', RejectAppealByManagerAPIView.as_view()),
    path('market/managers/vacancies/available_dates', GetVacanciesAvailableDatesForManager.as_view()),

    path('market/shifts', Shifts.as_view()),
    path('market/shifts/<int:record_id>', Shifts.as_view()),
    path('market/shifts/check', CheckUserShiftByManagerOrSecurityAPIView.as_view()),

    path('market/user_shifts', UserShiftsListAPIView.as_view()),
    path('market/user_shifts/<int:record_id>', UserShiftsRetrieveAPIView.as_view()),

    path('market/professions', Professions.as_view()),
    path('market/professions/suggest', suggest_profession),

    path('market/skills', Skills.as_view()),
]
