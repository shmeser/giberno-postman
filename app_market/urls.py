from django.urls import path

from app_market.views import Vacancies, Professions, suggest_profession, Skills, Distributors, Shops, VacanciesStats, \
    vacancies_suggestions, Shifts, similar_vacancies, ToggleLikeVacancy, \
    VacancyReviewsAPIView, ShopReviewsAPIView, DistributorReviewsAPIView, VacanciesClusteredMap, \
    ActiveVacanciesWithAppliersByDateForManagerListAPIView, VacancyByManagerRetrieveAPIView, ShiftAppeals, \
    SelfEmployedUserReviewsByAdminOrManagerAPIView, \
    ConfirmAppealByManagerAPIView, RejectAppealByManagerAPIView, \
    VacanciesActiveDatesForManagerListAPIView, VacanciesDistributors, SingleVacancyActiveDatesForManagerListAPIView, \
    ShiftAppealCancel, VacancyShiftsWithAppealsListForManagerAPIView, GetDocumentsForShift, MarketDocuments, \
    ShiftForManagers, ShiftAppealsForManagers, ConfirmedWorkers, ConfirmedWorkersProfessions, ConfirmedWorkersDates, \
    QRView, ShiftAppealComplete, CheckPassByManagerAPIView, AllowPassByManagerAPIView, work_location, \
    ShiftAppealCompleteByManager, \
    RefusePassByManagerAPIView, CheckPassBySecurityAPIView, RefusePassBySecurityAPIView, FireByManagerAPIView, \
    ProlongByManager

urlpatterns = [
    # Торговые сети
    path('market/distributors', Distributors.as_view()),
    path('market/distributors/<int:record_id>', Distributors.as_view()),
    path('market/distributors/<int:record_id>/reviews', DistributorReviewsAPIView.as_view()),

    # Магазины
    path('market/shops', Shops.as_view()),
    path('market/shops/<int:record_id>', Shops.as_view()),
    path('market/shops/<int:record_id>/reviews', ShopReviewsAPIView.as_view()),

    # Вакансии
    path('market/vacancies', Vacancies.as_view()),
    path('market/vacancies/<int:record_id>', Vacancies.as_view()),
    path('market/vacancies/<int:record_id>/similar', similar_vacancies),
    path('market/vacancies/<int:record_id>/reviews', VacancyReviewsAPIView.as_view()),
    path('market/vacancies/<int:record_id>/toggle_like', ToggleLikeVacancy.as_view()),  # TODO переделать на like/dislk

    path('market/vacancies/map', VacanciesClusteredMap.as_view()),
    path('market/vacancies/stats', VacanciesStats.as_view()),
    path('market/vacancies/distributors', VacanciesDistributors.as_view()),
    path('market/vacancies/suggestions', vacancies_suggestions),

    # Список своих откликов
    path('market/appeals', ShiftAppeals.as_view()),
    path('market/appeals/<int:record_id>', ShiftAppeals.as_view()),
    path('market/appeals/<int:record_id>/cancel', ShiftAppealCancel.as_view()),

    # Закрыть смену когда отображается таймер 15 мин после завершения
    path('market/appeals/<int:record_id>/complete', ShiftAppealComplete.as_view()),

    # Смены
    path('market/shifts', Shifts.as_view()),
    path('market/shifts/<int:record_id>', Shifts.as_view()),
    path('market/shifts/<int:record_id>/documents', GetDocumentsForShift.as_view()),

    # Смены пользователя
    # path('market/user_shifts', UserShiftsListAPIView.as_view()),
    # path('market/user_shifts/<int:record_id>', UserShiftsRetrieveAPIView.as_view()),

    # Geolocation
    path('market/location', work_location),

    # Профессии
    path('market/professions', Professions.as_view()),
    path('market/professions/suggest', suggest_profession),

    # Навыки
    path('market/skills', Skills.as_view()),

    # Документы
    path('market/documents', MarketDocuments.as_view()),
]

managers_urls = [
    # Список подтвержденных работников
    path('market/managers/self_employed', ConfirmedWorkers.as_view()),
    path('market/managers/self_employed/<int:record_id>', ConfirmedWorkers.as_view()),

    path('market/managers/self_employed/dates', ConfirmedWorkersDates.as_view()),
    path('market/managers/self_employed/professions', ConfirmedWorkersProfessions.as_view()),

    # Отзывы на самозанятых
    path('market/managers/self_employed/<int:record_id>/reviews',
         SelfEmployedUserReviewsByAdminOrManagerAPIView.as_view()),

    # Вакансии
    path('market/managers/vacancies', ActiveVacanciesWithAppliersByDateForManagerListAPIView.as_view()),
    path('market/managers/vacancies/active_dates', VacanciesActiveDatesForManagerListAPIView.as_view()),
    path('market/managers/vacancies/<int:record_id>', VacancyByManagerRetrieveAPIView.as_view()),
    path('market/managers/vacancies/<int:record_id>/active_dates',
         SingleVacancyActiveDatesForManagerListAPIView.as_view()),

    # Отклики на вакансии
    # TODO удалить после правок на андроиде
    path('market/managers/vacancies/<int:record_id>/appeals',
         VacancyShiftsWithAppealsListForManagerAPIView.as_view()),
    path('market/managers/vacancies/appeals/<int:record_id>/confirm', ConfirmAppealByManagerAPIView.as_view()),
    path('market/managers/vacancies/appeals/<int:record_id>/reject', RejectAppealByManagerAPIView.as_view()),
    ###

    # Проверки смен и пропусков
    path('market/qr', QRView.as_view()),

    path('market/managers/appeals/pass', CheckPassByManagerAPIView.as_view()),
    path('market/managers/appeals/<int:record_id>/pass/allow', AllowPassByManagerAPIView.as_view()),
    path('market/managers/appeals/<int:record_id>/pass/refuse', RefusePassByManagerAPIView.as_view()),

    # Управление откликами
    path('market/managers/appeals', VacancyShiftsWithAppealsListForManagerAPIView.as_view()),
    path('market/managers/appeals/complete', ShiftAppealCompleteByManager.as_view()),
    path('market/managers/appeals/<int:record_id>/confirm', ConfirmAppealByManagerAPIView.as_view()),
    path('market/managers/appeals/<int:record_id>/prolong', ProlongByManager.as_view()),
    path('market/managers/appeals/<int:record_id>/reject', RejectAppealByManagerAPIView.as_view()),
    path('market/managers/appeals/<int:record_id>/fire', FireByManagerAPIView.as_view()),

    # Список смен
    path('market/managers/shifts/<int:record_id>', ShiftForManagers.as_view()),
    # Отклики на смену
    path('market/managers/shifts/<int:record_id>/appeals', ShiftAppealsForManagers.as_view()),
]

security_urls = [
    path('market/security/appeals/pass', CheckPassBySecurityAPIView.as_view()),
    path('market/security/appeals/<int:record_id>/pass/refuse', RefusePassBySecurityAPIView.as_view()),
]

urlpatterns += managers_urls
urlpatterns += security_urls
