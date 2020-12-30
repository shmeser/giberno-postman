import requests
from constance import config
from django.http import JsonResponse
from django.views import View
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from app_bot.enums import TelegramBotNotificationType, TelegramBotMessageType, TelegramBotCommand
from app_bot.repositories import BotRepository
from backend.utils import get_request_body, timestamp_to_datetime, CP
from giberno.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_URL


class TelegramBotView(View):
    """
        Проверять по env какой сервер release stage develop
        Вводить команды на подписку событий с серверов указанных
        Подписываться на бота по коду

        /start <код>

        all_on - Включить все оповещения
        all_off - Отключить все оповещения
        debug_on - Включить оповещения об ошибках
        debug_off - Отключить оповещения об ошибках

    """

    def post(self, request, *args, **kwargs):
        t_data = get_request_body(request)
        # CP(fg='cyan').bold(t_data)

        if TelegramBotMessageType.PRIVATE.value in t_data:
            message_type = TelegramBotMessageType.PRIVATE.value
        elif TelegramBotMessageType.CHANNEL.value in t_data:
            message_type = TelegramBotMessageType.CHANNEL.value
        else:
            message_type = None

        incoming_data = t_data[message_type] if message_type else None

        t_chat = incoming_data.get("chat", None) if incoming_data else None
        text = incoming_data.get("text", '').strip().lower() if incoming_data else None

        if incoming_data is None or t_chat is None or text is None:
            return JsonResponse({
                "ok": "POST request processed"
            })

        chat = BotRepository.get_or_create_chat(
            chat_id=t_chat.get("id", None),
            chat_type=t_chat.get("type", None),
            chat_title=t_chat.get("title", None),
            username=t_chat.get("username", None),
            first_name=t_chat.get("first_name", None),
            last_name=t_chat.get("last_name", None)
        )

        entities = incoming_data.get('entities', None)

        is_bot_command = bool(list(filter(lambda x: x['type'] == 'bot_command', entities))) if entities else False
        bot_command = ''
        for v in TelegramBotCommand:
            bot_command = v.value if v.value in text else bot_command
        msg = ''

        # Если пришла команда
        if is_bot_command:
            # Проверяем команды
            if chat.approved and bot_command == TelegramBotCommand.START.value:
                msg = 'Бот уже активирован'

            if not chat.approved and bot_command == TelegramBotCommand.START.value and config.TELEGRAM_BOT_PASSWORD in text:
                # Если передан правильный пароль
                chat.approved = True
                chat.save()
                msg = f'Бот активирован для {t_chat.get("username", None) or t_chat.get("title", None)}'

            if not chat.approved:
                msg = f'Необходимо получить доступ к боту, отправив команду "/start <password>"'
            elif TelegramBotCommand.has_value(bot_command):
                if bot_command == TelegramBotCommand.ALL_ON.value:
                    chat.notification_types = [
                        TelegramBotNotificationType.DEBUG.value,
                    ]
                    chat.save()
                    msg = f'Включены все оповещения'

                if bot_command == TelegramBotCommand.ALL_OFF.value and chat.approved:
                    chat.notification_types = None
                    chat.save()
                    msg = f'Отключены все оповещения'

                if bot_command == TelegramBotCommand.DEBUG_ON.value and chat.approved:
                    if not chat.notification_types:
                        chat.notification_types = [TelegramBotNotificationType.DEBUG.value]
                    elif TelegramBotNotificationType.DEBUG.value not in chat.notification_types:
                        chat.notification_types.append(TelegramBotNotificationType.DEBUG.value)
                    chat.save()
                    msg = f'Включены оповещения об ошибках'

                if bot_command == TelegramBotCommand.DEBUG_OFF.value and chat.approved:
                    if chat.notification_types:
                        chat.notification_types.remove(TelegramBotNotificationType.DEBUG.value)
                    chat.save()
                    msg = f'Отключены оповещения об ошибках'
            else:
                msg = f"Неизвестная комманда"

        # Если пришло обычное сообщение
        else:
            if chat.approved:
                msg = f"Сообщение, отправленное боту: {text}"
            else:
                msg = f'Необходимо получить доступ к боту, отправив команду "/start <password>"'

        self.send_message(msg, t_chat["id"])

        message_data = {
            "message_id": incoming_data['message_id'],
            "date": timestamp_to_datetime(incoming_data['date'], milliseconds=False),
            "text": text,
            "chat_type": t_chat.get("type", None)
        }

        if message_type == TelegramBotMessageType.PRIVATE.value:
            message_data["is_bot"] = incoming_data['from'].get('is_bot', None)
            message_data["from_id"] = incoming_data['from'].get('id', None)
            message_data["username"] = incoming_data['from'].get('username', None)
            message_data["first_name"] = incoming_data['from'].get('first_name', None)
            message_data["last_name"] = incoming_data['from'].get('last_name', None)
            message_data["language_code"] = incoming_data['from'].get('language_code', None)

        if message_type == TelegramBotMessageType.CHANNEL.value:
            message_data["title"] = incoming_data['sender_chat'].get('title', None)

        BotRepository.create_message(chat, **message_data)

        BotRepository.create_message(chat, **{
            "is_bot": True,
            "text": msg,
            "username": "GibernoBot",
            "chat_type": t_chat.get("type", None)
        })

        CP(fg='cyan').bold(t_data)

        return JsonResponse({
            "ok": "POST request processed",
        })

    @staticmethod
    def send_message(message, chat_id):
        data = {
            "chat_id": chat_id,
            "text": message,
        }
        response = requests.post(
            f"{TELEGRAM_URL}{TELEGRAM_BOT_TOKEN}/sendMessage", data=data
        )

        CP(fg='yellow').bold(str(TELEGRAM_BOT_TOKEN))
        CP(fg='yellow').bold(str(response))


class TestView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        a = request['asda']
        return JsonResponse({
            "data": a
        })
