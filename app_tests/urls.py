from django.urls import path

from app_tests.views import GetUserTokenTestAPIView, SendTestPush, TestBonusesDeposit, TestMoneyPay

urlpatterns = [
    path('get_access_token_by_user_id/<int:pk>', GetUserTokenTestAPIView.as_view()),

    path('notifications/send', SendTestPush.as_view()),

    path('bonus/deposit', TestBonusesDeposit.as_view()),
    path('bonus/withdraw', TestBonusesDeposit.as_view()),

    # Finances
    path('money/pay', TestMoneyPay.as_view()),
    path('money/reward', TestMoneyPay.as_view()),
    path('money/penalty', TestMoneyPay.as_view()),
]
