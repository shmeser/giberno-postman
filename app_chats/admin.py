from django.contrib import admin

from app_chats.models import Chat, ChatUser, Message, MessageStat
from backend.mixins import FormattedAdmin


@admin.register(Chat)
class ChatAdmin(FormattedAdmin):
    list_display = [
        'title', 'created_at'
    ]


@admin.register(ChatUser)
class ChatUserAdmin(FormattedAdmin):
    list_display = [
        'chat_id', 'user_id', 'blocked_at', 'created_at'
    ]


@admin.register(Message)
class MessageAdmin(FormattedAdmin):
    list_display = [
        'chat_id', 'title', 'text', 'message_type', 'user_id', 'form_status', 'read_at'
    ]


@admin.register(MessageStat)
class MessageStatAdmin(FormattedAdmin):
    list_display = [
        'message_id', 'user_id', 'is_read'
    ]
