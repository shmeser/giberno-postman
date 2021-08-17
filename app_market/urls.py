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
    ProlongByManager, CancelFiringByManager, PushSettingsForConfirmedWorkers, Partners, PartnersCategories, \
    Achievements, Advertisements, Orders, Coupons, GetDocumentsForPartner, Finances, get_my_money, \
    PartnersShopDocuments, AdminShops, AdminVacancies, AdminAppeals, \
    AdminShifts, AdminPositions, AdminProfessions

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

    # Geolocation
    path('market/location', work_location),

    # Профессии
    path('market/professions', Professions.as_view()),
    path('market/professions/suggest', suggest_profession),

    # Навыки
    path('market/skills', Skills.as_view()),

    # Документы
    path('market/documents', MarketDocuments.as_view()),

    # Партнеры
    path('market/partners/documents', PartnersShopDocuments.as_view()),
    path('market/partners', Partners.as_view()),
    path('market/partners/<int:record_id>', Partners.as_view()),
    path('market/partners/<int:record_id>/documents', GetDocumentsForPartner.as_view()),
    path('market/partners/categories', PartnersCategories.as_view()),

    # Достижения
    path('market/achievements', Achievements.as_view()),
    path('market/achievements/<int:record_id>', Achievements.as_view()),

    # Рекламные блоки
    path('market/ads', Advertisements.as_view()),
    path('market/ads/<int:record_id>', Advertisements.as_view()),

    # Заказы
    path('market/orders', Orders.as_view()),

    # Купоны
    path('market/coupons', Coupons.as_view()),

    # Финансы с группировками по дням, месяцам, годам
    path('market/finances', Finances.as_view()),
    # Баланс по разным счетам
    path('market/finances/money', get_my_money),
]

managers_urls = [
    # Список подтвержденных работников
    path('market/managers/self_employed', ConfirmedWorkers.as_view()),
    path('market/managers/self_employed/<int:record_id>', ConfirmedWorkers.as_view()),
    path('market/managers/self_employed/<int:record_id>/settings', PushSettingsForConfirmedWorkers.as_view()),

    path('market/managers/self_employed/dates', ConfirmedWorkersDates.as_view()),
    path('market/managers/self_employed/professions', ConfirmedWorkersProfessions.as_view()),

    # Отзывы на самозанятых
    path('market/managers/self_employed/<int:user_id>/reviews',
         SelfEmployedUserReviewsByAdminOrManagerAPIView.as_view()),

    # Вакансии
    path('market/managers/vacancies', ActiveVacanciesWithAppliersByDateForManagerListAPIView.as_view()),
    path('market/managers/vacancies/active_dates', VacanciesActiveDatesForManagerListAPIView.as_view()),
    path('market/managers/vacancies/<int:record_id>', VacancyByManagerRetrieveAPIView.as_view()),
    path('market/managers/vacancies/<int:record_id>/active_dates',
         SingleVacancyActiveDatesForManagerListAPIView.as_view()),

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
    path('market/managers/appeals/<int:record_id>/fire/cancel', CancelFiringByManager.as_view()),

    # Список смен
    path('market/managers/shifts/<int:record_id>', ShiftForManagers.as_view()),
    # Отклики на смену
    path('market/managers/shifts/<int:record_id>/appeals', ShiftAppealsForManagers.as_view()),
]

security_urls = [
    path('market/security/appeals/pass', CheckPassBySecurityAPIView.as_view()),
    path('market/security/appeals/<int:record_id>/pass/refuse', RefusePassBySecurityAPIView.as_view()),
]

admin_panel = [

    path('admin/market/shops', AdminShops.as_view()),
    path('admin/market/vacancies', AdminVacancies.as_view()),
    path('admin/market/appeals', AdminAppeals.as_view()),
    path('admin/market/shifts', AdminShifts.as_view()),
    path('admin/market/positions', AdminPositions.as_view()),
    path('admin/market/professions', AdminProfessions.as_view()),

]

urlpatterns += admin_panel

urlpatterns += managers_urls
urlpatterns += security_urls
urlpatterns += admin_panel
