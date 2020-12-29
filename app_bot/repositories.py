from django.db.models import Q

from app_bot.enums import BotNotificationType
from app_bot.models import BotChat, BotMessage


class BotRepository:
    @staticmethod
    def get_or_create_chat(chat_id, chat_type, chat_title, username, first_name, last_name):
        chat, created = BotChat.objects.get_or_create(
            chat_id=chat_id,
            type=chat_type,
            title=chat_title,
            username=username,
            first_name=first_name,
            last_name=last_name
        )
        return chat

    @staticmethod
    def create_message(chat, **kwargs):
        return BotMessage.objects.create(
            chat=chat,
            **kwargs
        )

    @staticmethod
    def get_chats_by_notification_types(notification_types=BotNotificationType.DEBUG.value, approved=True):
        return BotChat.objects.filter(
            approved=approved,
            notification_types__contains=[notification_types]
        )

    @staticmethod
    def get_chats_with_no_env(approved=True):
        chats = BotChat.objects.filter(
            Q(
                approved=approved,
                notification_types__isnull=True
            ) |
            Q(
                approved=approved,
                notification_types__len=0
            )
        )

        return chats
