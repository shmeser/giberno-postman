from django.urls import path

from app_market import views

urlpatterns = [
    # Торговые сети
    path('market/distributors', views.Distributors.as_view()),
    path('market/distributors/<int:record_id>', views.Distributors.as_view()),
    path('market/distributors/<int:record_id>/reviews', views.DistributorReviewsAPIView.as_view()),

    # Магазины
    path('market/shops', views.Shops.as_view()),
    path('market/shops/<int:record_id>', views.Shops.as_view()),
    path('market/shops/<int:record_id>/reviews', views.ShopReviewsAPIView.as_view()),

    # Вакансии
    path('market/vacancies', views.Vacancies.as_view()),
    path('market/vacancies/<int:record_id>', views.Vacancies.as_view()),
    path('market/vacancies/<int:record_id>/similar', views.similar_vacancies),
    path('market/vacancies/<int:record_id>/reviews', views.VacancyReviewsAPIView.as_view()),
    path('market/vacancies/<int:record_id>/toggle_like', views.ToggleLikeVacancy.as_view()),
    # TODO переделать на like/dislk

    path('market/vacancies/map', views.VacanciesClusteredMap.as_view()),
    path('market/vacancies/stats', views.VacanciesStats.as_view()),
    path('market/vacancies/distributors', views.VacanciesDistributors.as_view()),
    path('market/vacancies/suggestions', views.vacancies_suggestions),

    # Список своих откликов
    path('market/appeals', views.ShiftAppeals.as_view()),
    path('market/appeals/<int:record_id>', views.ShiftAppeals.as_view()),
    path('market/appeals/<int:record_id>/cancel', views.ShiftAppealCancel.as_view()),

    # Закрыть смену когда отображается таймер 15 мин после завершения
    path('market/appeals/<int:record_id>/complete', views.ShiftAppealComplete.as_view()),

    # Смены
    path('market/shifts', views.Shifts.as_view()),
    path('market/shifts/<int:record_id>', views.Shifts.as_view()),
    path('market/shifts/<int:record_id>/documents', views.GetDocumentsForShift.as_view()),

    # Geolocation
    path('market/location', views.work_location),

    # Профессии
    path('market/professions', views.Professions.as_view()),
    path('market/professions/suggest', views.suggest_profession),

    # Навыки
    path('market/skills', views.Skills.as_view()),

    # Документы
    path('market/documents', views.MarketDocuments.as_view()),

    # Партнеры
    path('market/partners/documents', views.PartnersShopDocuments.as_view()),
    path('market/partners', views.Partners.as_view()),
    path('market/partners/<int:record_id>', views.Partners.as_view()),
    path('market/partners/<int:record_id>/documents', views.GetDocumentsForPartner.as_view()),
    path('market/partners/categories', views.PartnersCategories.as_view()),

    # Достижения
    path('market/achievements', views.Achievements.as_view()),
    path('market/achievements/<int:record_id>', views.Achievements.as_view()),

    # Рекламные блоки
    path('market/ads', views.Advertisements.as_view()),
    path('market/ads/<int:record_id>', views.Advertisements.as_view()),

    # Заказы
    path('market/orders', views.Orders.as_view()),

    # Купоны
    path('market/coupons', views.Coupons.as_view()),

    # Финансы с группировками по дням, месяцам, годам
    path('market/finances', views.Finances.as_view()),
    path('market/finances/transactions', views.Transactions.as_view()),
    # Баланс по разным счетам
    path('market/finances/money', views.get_my_money),
    path('market/finances/receipts', views.Receipts.as_view()),
    path('market/finances/receipts/<int:record_id>', views.Receipts.as_view()),
    path('market/finances/receipts/<int:record_id>/cancel', views.CancelReceipt.as_view()),
]

managers_urls = [
    # Список подтвержденных работников
    path('market/managers/self_employed', views.ConfirmedWorkers.as_view()),
    path('market/managers/self_employed/<int:record_id>', views.ConfirmedWorkers.as_view()),
    path('market/managers/self_employed/<int:record_id>/settings', views.PushSettingsForConfirmedWorkers.as_view()),

    path('market/managers/self_employed/dates', views.ConfirmedWorkersDates.as_view()),
    path('market/managers/self_employed/professions', views.ConfirmedWorkersProfessions.as_view()),

    # Отзывы на самозанятых
    path('market/managers/self_employed/<int:user_id>/reviews',
         views.SelfEmployedUserReviewsByAdminOrManagerAPIView.as_view()),

    # Вакансии
    path('market/managers/vacancies', views.ActiveVacanciesWithAppliersByDateForManagerListAPIView.as_view()),
    path('market/managers/vacancies/active_dates', views.VacanciesActiveDatesForManagerListAPIView.as_view()),
    path('market/managers/vacancies/<int:record_id>', views.VacancyByManagerRetrieveAPIView.as_view()),
    path('market/managers/vacancies/<int:record_id>/active_dates', views.SingleVacancyActiveDatesForManager.as_view()),

    # Проверки смен и пропусков
    path('market/qr', views.QRView.as_view()),

    path('market/managers/appeals/pass', views.CheckPassByManagerAPIView.as_view()),
    path('market/managers/appeals/<int:record_id>/pass/allow', views.AllowPassByManagerAPIView.as_view()),
    path('market/managers/appeals/<int:record_id>/pass/refuse', views.RefusePassByManagerAPIView.as_view()),

    # Управление откликами
    path('market/managers/appeals', views.VacancyShiftsWithAppealsListForManagerAPIView.as_view()),
    path('market/managers/appeals/complete', views.ShiftAppealCompleteByManager.as_view()),
    path('market/managers/appeals/<int:record_id>/confirm', views.ConfirmAppealByManagerAPIView.as_view()),
    path('market/managers/appeals/<int:record_id>/prolong', views.ProlongByManager.as_view()),
    path('market/managers/appeals/<int:record_id>/reject', views.RejectAppealByManagerAPIView.as_view()),
    path('market/managers/appeals/<int:record_id>/fire', views.FireByManagerAPIView.as_view()),
    path('market/managers/appeals/<int:record_id>/fire/cancel', views.CancelFiringByManager.as_view()),

    # Список смен
    path('market/managers/shifts/<int:record_id>', views.ShiftForManagers.as_view()),
    # Отклики на смену
    path('market/managers/shifts/<int:record_id>/appeals', views.ShiftAppealsForManagers.as_view()),
]

security_urls = [
    path('market/security/appeals/pass', views.CheckPassBySecurityAPIView.as_view()),
    path('market/security/appeals/<int:record_id>/pass/refuse', views.RefusePassBySecurityAPIView.as_view()),
]

admin_panel = [

    path('admin/market/distributors', views.AdminDistributors.as_view()),
    path('admin/market/distributors/<int:record_id>', views.AdminDistributor.as_view()),
    path('admin/market/distributors/categories', views.AdminDistributorCategories.as_view()),
    path('admin/market/distributors/categories/<int:record_id>', views.AdminDistributorCategory.as_view()),

    path('admin/market/structures', views.AdminStructures.as_view()),
    path('admin/market/structures/<int:record_id>', views.AdminStructure.as_view()),

    path('admin/market/shops', views.AdminShops.as_view()),
    path('admin/market/shops/<int:record_id>', views.AdminShop.as_view()),

    path('admin/market/vacancies', views.AdminVacancies.as_view()),
    path('admin/market/vacancies/<int:record_id>', views.AdminVacancy.as_view()),

    path('admin/market/professions', views.AdminProfessions.as_view()),
    path('admin/market/professions/<int:record_id>', views.AdminProfession.as_view()),

    path('admin/market/positions', views.AdminPositions.as_view()),
    path('admin/market/positions/<int:record_id>', views.AdminPosition.as_view()),

    path('admin/market/shifts', views.AdminShifts.as_view()),
    path('admin/market/shifts/<int:record_id>', views.AdminShift.as_view()),

    path('admin/market/appeals', views.AdminAppeals.as_view()),
    path('admin/market/appeals/<int:record_id>', views.AdminAppeal.as_view()),

    path('admin/market/coupons', views.AdminCoupons.as_view()),
    path('admin/market/coupons/<int:record_id>', views.AdminCoupon.as_view()),

    path('admin/market/partners', views.AdminPartners.as_view()),
    path('admin/market/partners/<int:record_id>', views.AdminPartner.as_view()),

    path('admin/market/finances/receipts', views.AdminReceipts.as_view()),
    path('admin/market/finances/receipts/<int:record_id>', views.AdminReceipts.as_view()),

]

urlpatterns += admin_panel

urlpatterns += managers_urls
urlpatterns += security_urls
urlpatterns += admin_panel
