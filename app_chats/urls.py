from django.urls import path

from app_chats.views import Chats, Messages, ReadMessages, block_chat, unblock_chat, market_data

urlpatterns = [
    path('chats', Chats.as_view()),
    path('chats/<int:record_id>', Chats.as_view()),

    path('chats/<int:record_id>/market', market_data),
    path('chats/<int:record_id>/block', block_chat),
    path('chats/<int:record_id>/unblock', unblock_chat),
    path('chats/<int:record_id>/messages', Messages.as_view()),
    path('chats/<int:record_id>/messages/read', ReadMessages.as_view()),
]
