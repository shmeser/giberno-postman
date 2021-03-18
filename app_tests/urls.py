from django.urls import path

from app_tests.views import GetUserTokenTestAPIView, SendTestPush

urlpatterns = [
    path('get_access_token_by_user_id/<int:pk>', GetUserTokenTestAPIView.as_view()),
    path('notifications/send', SendTestPush.as_view())
]
