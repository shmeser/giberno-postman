from datetime import timedelta

from celery import group
from django.db.models import Max
from django.utils.timezone import now

from app_sockets.controllers import SocketController
from app_sockets.enums import AvailableRoom, AvailableVersion
from app_sockets.mappers import RoutingMapper
from backend.utils import TruncMilliecond
from giberno.celery import app
from giberno.settings import AUTO_SWITCH_TO_BOT_MIN
from .enums import ChatManagerState, ChatMessageType, ChatMessageIconType
from .models import Chat

_ITEMS_PER_ITERATION = 5


@app.task
def check_abandoned_chats():
    # Ищем все чаты, у которых state
    # NEED_MANAGER = 1
    # MANAGER_CONNECTED = 2
    # и нет активности более 15 минут и переводим их в BOT_IS_USED = 0
    abandoned_chats = Chat.objects.annotate(
        last_message_created_at=Max(
            # Округляем до миллисекунд, так как в бд DateTimeField хранит с точностью до МИКРОсекунд
            TruncMilliecond('messages__created_at')
        )
    ).filter(
        state__in=[ChatManagerState.NEED_MANAGER.value, ChatManagerState.MANAGER_CONNECTED.value],
        last_message_created_at__lt=now() - timedelta(minutes=AUTO_SWITCH_TO_BOT_MIN)
    )

    jobs = group(
        [auto_update_abandoned_chat_state.s(chat.id) for chat in abandoned_chats])
    jobs.apply_async()


@app.task
def auto_update_abandoned_chat_state(chat_id):
    version = AvailableVersion.V1_0.value
    _AUTO_SWITCH_TEXT = 'Чат перевён на бота'

    chat_repository = RoutingMapper.room_repository(
        version=version, room_name=AvailableRoom.CHATS.value)
    message_repository = RoutingMapper.room_repository(
        version=version, room_name=AvailableRoom.MESSAGES.value)

    chat = chat_repository().get_by_id(chat_id)

    chat.updated_at = now()
    chat.state = ChatManagerState.BOT_IS_USED.value
    chat.save()

    chat.active_managers.clear()  # Убираем всех активных менеджеров

    bot_message_serialized = message_repository(chat_id=chat_id).save_bot_message(
        {
            'message_type': ChatMessageType.INFO.value,
            'text': _AUTO_SWITCH_TEXT,
            'icon_type': ChatMessageIconType.SUPPORT.value
        }
    )

    SocketController(
        version=AvailableVersion.V1_0.value,
        room_name=AvailableRoom.CHATS.value
    ).send_chat_state(
        state=ChatManagerState.BOT_IS_USED.value,
        chat_id=chat_id
    )

    SocketController(
        version=AvailableVersion.V1_0.value,
        room_name=AvailableRoom.CHATS.value
    ).send_chat_message(chat_id=chat_id, prepared_message=bot_message_serialized)
