import requests
from constance import config
from django.http import JsonResponse
from django.views import View
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView

from app_bot.enums import BotNotificationType
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
        t_message = t_data["message"] if "message" in t_data else None
        t_channel_post = t_data["channel_post"] if "channel_post" in t_data else None

        incoming_data = t_message or t_channel_post

        t_chat = incoming_data["chat"] if "chat" in incoming_data else None
        text = incoming_data["text"].strip().lower() if incoming_data and 'text' in incoming_data else None

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

        # Если пришла команда
        if "entities" in incoming_data and incoming_data['entities']:
            msg = None
            for entity in incoming_data['entities']:
                if entity['type'] == 'bot_command':
                    # Проверяем команды
                    if '/start' in text and config.TELEGRAM_BOT_PASSWORD in text:
                        # Если передан правильный пароль
                        chat.approved = True
                        chat.save()
                        msg = f'Бот активирован для {t_chat["username"]}'

                    if '/all_on' in text and chat.approved:
                        chat.notification_types = [
                            BotNotificationType.DEBUG.value,
                            BotNotificationType.SUBSCRIPTION_PAYED.value,
                            BotNotificationType.PURCHASE_MADE.value,
                        ]
                        chat.save()
                        msg = f'Включены все оповещения'

                    if '/all_off' in text and chat.approved:
                        chat.notification_types = None
                        chat.save()
                        msg = f'Отключены все оповещения'

                    if '/debug_on' in text and chat.approved:
                        if not chat.notification_types:
                            chat.notification_types = [BotNotificationType.DEBUG.value]
                        elif BotNotificationType.DEBUG.value not in chat.notification_types:
                            chat.notification_types.append(BotNotificationType.DEBUG.value)
                        chat.save()
                        msg = f'Включены оповещения об ошибках'

                    if '/debug_off' in text and chat.approved:
                        if chat.notification_types:
                            chat.notification_types.remove(BotNotificationType.DEBUG.value)
                        chat.save()
                        msg = f'Отключены оповещения об ошибках'

            if msg:
                self.send_message(msg, t_chat["id"])
            else:
                msg = f"Необходимо получить доступ к боту, отправив команду /start <password>"
                self.send_message(msg, t_chat["id"])

        # Если пришло обычное сообщение
        else:
            if chat.approved:
                msg = f"Сообщение, отправленное боту: {text}"
                self.send_message(msg, t_chat["id"])
            else:
                msg = f'Необходимо получить доступ к боту, отправив команду "/start <password>"'
                self.send_message(msg, t_chat["id"])

        BotRepository.create_message(chat, **{
            "message_id": incoming_data['message_id'],
            "date": timestamp_to_datetime(t_message['date'], milliseconds=False),
            "text": text,
            "is_bot": incoming_data['from']['is_bot'],
            "from_id": t_message['from']['id'],
            "username": t_message['from']['username'] if "username" in t_message['from'] else None,
            "first_name": t_message['from']['first_name'] if "first_name" in t_message['from'] else None,
            "last_name": t_message['from']['last_name'] if "last_name" in t_message['from'] else None,
            "language_code": t_message['from']['language_code'] if "language_code" in t_message['from'] else None,
        })

        BotRepository.create_message(chat, **{
            "is_bot": True,
            "text": msg,
            "username": "GibernoBot"
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
        CP(fg='yellow').bold(response)


class TestView(APIView):
    permission_classes = (AllowAny,)

    def get(self, request):
        a = request['asda']
        return JsonResponse({
            "data": a
        })
