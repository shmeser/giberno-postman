from django.contrib.gis import admin

from app_bot.models import BotChat, BotMessage, Intent, IntentRequest, IntentResponse
from backend.mixins import FormattedAdmin


@admin.register(Intent)
class IntentAdmin(FormattedAdmin):
    list_display = [
        'code', 'topic', 'created_at'
    ]
    list_filter = ['code']


@admin.register(IntentRequest)
class IntentRequestAdmin(FormattedAdmin):
    list_display = [
        'intent_id', 'text', 'created_at'
    ]

    list_filter = ['intent_id']


@admin.register(IntentResponse)
class IntentResponseAdmin(FormattedAdmin):
    list_display = [
        'intent_id', 'text', 'created_at'
    ]
    list_filter = ['intent_id']


@admin.register(BotChat)
class BotChatAdmin(FormattedAdmin):
    list_display = ("id", "chat_id", "type", "username", "first_name", "last_name", "title", "approved",
                    "notification_types", "created_at")

    list_filter = ("type", "approved",)


@admin.register(BotMessage)
class BotMessageAdmin(FormattedAdmin):
    list_display = ("id", "chat", "from_id", "is_bot", "username", "text", "created_at")

    list_filter = ("is_bot",)

    raw_id_fields = ["chat", ]
