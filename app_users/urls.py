from django.urls import path

from app_users.views import Users

urlpatterns = [
    path('users', Users.as_view()),
]
