from django.contrib.gis import admin

from app_bot.models import BotChat, BotMessage


@admin.register(BotChat)
class BotChatAdmin(admin.OSMGeoAdmin):
    list_display = ("id", "chat_id", "type", "username", "first_name", "last_name", "title", "approved",
                    "notification_types", "created_at")

    list_filter = ("type", "approved",)


@admin.register(BotMessage)
class BotMessageAdmin(admin.OSMGeoAdmin):
    list_display = ("id", "chat", "from_id", "is_bot", "username", "text", "created_at")

    list_filter = ("is_bot",)

    raw_id_fields = ["chat", ]
