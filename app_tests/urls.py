from django.urls import path

from app_tests.views import GetUserTokenTestAPIView, SendTestPush, SeedDataForMarketAppAPIView, \
    GetUsersIdListByTypeAPIView, TestBonusesDeposit

urlpatterns = [
    path('get_access_token_by_user_id/<int:pk>', GetUserTokenTestAPIView.as_view()),
    path('notifications/send', SendTestPush.as_view()),
    path('deposit/bonus', TestBonusesDeposit.as_view()),
    path('seed_data_for_market_app', SeedDataForMarketAppAPIView.as_view()),
    path('get_users_id_list_by_type/<int:type>', GetUsersIdListByTypeAPIView.as_view())
]
