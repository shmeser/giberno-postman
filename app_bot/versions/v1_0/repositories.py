from app_bot.enums import TelegramBotNotificationType
from app_bot.models import BotChat, BotMessage


class TelegramBotRepository:
    @staticmethod
    def get_or_create_chat(chat_id, chat_type, chat_title, username, first_name, last_name):
        chat, created = BotChat.objects.get_or_create(
            defaults={
                'title': chat_title,
                'username': username,
                'first_name': first_name,
                'last_name': last_name
            },
            chat_id=chat_id,
            type=chat_type
        )
        return chat

    @staticmethod
    def create_message(chat, **kwargs):
        return BotMessage.objects.create(
            chat=chat,
            **kwargs
        )

    @staticmethod
    def get_chats_by_notification_types(notification_types=TelegramBotNotificationType.DEBUG.value, approved=True):
        return BotChat.objects.filter(
            approved=approved,
            notification_types__contains=[notification_types]
        )
