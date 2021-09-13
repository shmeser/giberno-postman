from django.urls import path

from appcraft_nalog_sdk import views

urlpatterns = [
    path('update_processing_statuses', views.UpdateStatuses.as_view()),
    path('status', views.StatusView.as_view()),
    path('notifications', views.NotificationsView.as_view()),
    path('bind', views.BindView.as_view()),
    path('income', views.PostIncomeView.as_view()),
    path('cancel-reasons', views.CancelReasons.as_view()),
    path('granted-permissions', views.GrantedPermissionsView.as_view()),
    path('platform-registration', views.PlatformRegistrationView.as_view()),
    path('get-newly-unbound-taxpayers-request', views.GetNewlyUnboundTaxpayersRequest.as_view()),
    path('get-payment-documents_request', views.GetPaymentDocumentsRequest.as_view()),
]
