import io
import logging
import os
import traceback

import requests

from app_bot.enums import TelegramBotNotificationType
from backend.enums import Environment
from backend.utils import get_request_body, get_request_headers
from giberno.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_URL


class TelegramFormatter(logging.Formatter):

    def recursive_tab_str(self, data_dict, tab=0):
        if not isinstance(data_dict, dict):
            return data_dict
        brackets_ident = ''
        tab_str = "  "
        values_ident = tab_str
        iteration = 0
        keys_count = len(data_dict)
        i = 0

        while i < tab:
            brackets_ident += tab_str
            values_ident += tab_str
            i += 1
        result = brackets_ident + "{\n"
        for k, v in data_dict.items():
            iteration += 1
            eol = ",\n" if keys_count != iteration else ""

            if isinstance(v, dict):
                result += values_ident + f"'{k}': {self.recursive_tab_str(v, tab + 1)}" + eol
            else:
                result += values_ident + f"'{k}': {v}" + eol

        return result + "\n" + brackets_ident + "}"

    meta_attrs = [
        'REMOTE_HOST',
        'SERVER_NAME',
        'SERVER_PORT',
        'REQUEST_METHOD',
        'PATH_INFO',
        'QUERY_STRING',
    ]
    limit = -1  # default per logging.Formatter is None

    def format(self, record):
        s = f"SERVER: {os.getenv('ENVIRONMENT', Environment.LOCAL.value)}"
        s += f"\nUSER: {record.request.user}"

        for attr in self.meta_attrs:
            if attr in record.request.META:
                s += f"\n{attr}: {record.request.META[attr]}"

        if record.request.headers:
            headers = get_request_headers(record.request)
            s += f"\nHEADERS: {self.recursive_tab_str(headers)}"

        if record.request.body:
            body = get_request_body(record.request)
            s += f"\nBODY: {self.recursive_tab_str(body)}"

        s += '\n\n ------------------------ \n\n'
        s += super().format(record)

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


class TelegramBotSender:
    @staticmethod
    def send_message(message, notification_type):
        from app_bot.versions.v1_0.repositories import TelegramBotRepository

        if notification_type == TelegramBotNotificationType.DEBUG.value:
            chats = TelegramBotRepository.get_chats_by_notification_types(
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

            TelegramBotRepository.create_message(chat, **{
                "is_bot": True,
                "text": message,
                "username": "GibernoBot",
                "chat_type": chat.type
            })

            print(f'>>>> TELEGRAM_URL <<<< {TELEGRAM_URL} | >>>> TELEGRAM_BOT_TOKEN <<<< {TELEGRAM_BOT_TOKEN}')
            requests.post(
                f"{TELEGRAM_URL}{TELEGRAM_BOT_TOKEN}/sendMessage", data=prepared_data
            )


class TelegramBotLogger(logging.Handler):
    def __init__(self, *args, **kwargs):
        super().__init__()

        self.setFormatter(TelegramFormatter())

    def emit(self, record):
        print('>>>>>>>>>>>>>>>>> TELEGRAM ERROR SENDING <<<<<<<<<<<<<<<<<')
        TelegramBotSender.send_message(self.format(record), TelegramBotNotificationType.DEBUG.value)
