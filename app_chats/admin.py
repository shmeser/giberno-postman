from django.contrib import admin

from app_chats.models import Chat, ChatUser, Message
from app_users.models import UserProfile
from backend.mixins import FormattedAdmin


@admin.register(Chat)
class ChatAdmin(FormattedAdmin):
    inlines = [
        UserProfile
    ]

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
        'chat_id', 'text', 'message_type', 'owner_ct_name', 'owner_id', 'form_status', 'read_at'
    ]
