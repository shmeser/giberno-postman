import io
import logging
import os
import traceback

import requests
from requests import Response

from app_bot.enums import TelegramBotNotificationType
from giberno.environment.environments import Environment
from giberno.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_URL


class TelegramFormatter(logging.Formatter):
    meta_attrs = [
        'REMOTE_ADDR',
        'HOSTNAME',
        'HTTP_REFERER'
    ]
    limit = -1  # default per logging.Formatter is None

    def format(self, record):
        s = super().format(record)

        s += "\n{attr}: {value}".format(
            attr='USER',
            value=record.request.user
        )
        for attr in self.meta_attrs:
            if attr in record.request.META:
                s += "\n{attr}: {value}".format(
                    attr=attr,
                    value=record.request.META[attr]
                )

        s += f"\nSERVER: {os.getenv('ENVIRONMENT', Environment.LOCAL.value)}"

        return s

    def formatException(self, ei):
        sio = io.StringIO()
        tb = ei[2]

        traceback.print_exception(ei[0], ei[1], tb, self.limit, sio)
        s = sio.getvalue()
        sio.close()
        if s[-1:] == "\n":
            s = s[:-1]
        return s


class BotSender:
    @staticmethod
    def send_message(message, notification_type):
        from app_bot.repositories import BotRepository

        if notification_type == TelegramBotNotificationType.DEBUG.value:
            chats = BotRepository.get_chats_by_notification_types(
                TelegramBotNotificationType.DEBUG.value,
                approved=True
            )
        else:
            chats = []

        for chat in chats:
            prepared_data = {
                "chat_id": chat.chat_id,
                "text": message,
                "parse_mode": 'HTML',
            }

            BotRepository.create_message(chat, **{
                "is_bot": True,
                "text": message,
                "username": "GibernoBot",
                "chat_type": chat.type
            })

            requests.post(
                f"{TELEGRAM_URL}{TELEGRAM_BOT_TOKEN}/sendMessage", data=prepared_data
            )


class BotLogger(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__()

        self.setFormatter(TelegramFormatter())

    def emit(self, record):
        BotSender.send_message(self.format(record), TelegramBotNotificationType.DEBUG.value)
