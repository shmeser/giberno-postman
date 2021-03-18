from django.urls import path

from app_chats.views import Chats, Messages

urlpatterns = [
    path('chats', Chats.as_view()),
    path('chats/<record_id:int>', Chats.as_view()),

    path('chats/<record_id:int>/messages', Messages.as_view()),
]
