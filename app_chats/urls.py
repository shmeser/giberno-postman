from django.urls import path

from app_chats.views import Chats, Messages

urlpatterns = [
    path('chats', Chats.as_view()),
    path('chats/<int:record_id>', Chats.as_view()),

    path('chats/<int:record_id>/messages', Messages.as_view()),
]
