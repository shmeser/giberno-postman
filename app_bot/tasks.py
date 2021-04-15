from loguru import logger

from app_sockets.controllers import SocketController
from app_sockets.enums import AvailableRoom, AvailableVersion
from app_sockets.mappers import RoutingMapper
from app_users.enums import AccountType
from giberno.celery import app


@app.task
def delayed_checking_for_bot_reply(version, chat_id, user_id, message_text):
    try:
        user_repository = RoutingMapper.room_repository(
            version=version, room_name=AvailableRoom.USERS.value)
        bot_repository = RoutingMapper.room_repository(
            version=version, room_name=AvailableRoom.BOT.value)
        message_repository = RoutingMapper.room_repository(
            version=version, room_name=AvailableRoom.MESSAGES.value)

        user = user_repository().get_by_id(user_id)

        # Проверяем необходимость отправки сообщения в чат от имени бота
        if user is None or user.account_type != AccountType.SELF_EMPLOYED.value:
            return

        # TODO Определить тип ответа - список документов, форма, обычное сообщение и т.д.

        reply = bot_repository.get_response(message_text)

        bot_message_serialized = message_repository(chat_id=chat_id).save_bot_message(
            {
                'message_type': 1,
                'text': reply,
                'command_data': None
            }
        )

        SocketController(
            version=AvailableVersion.V1_0.value,
            room_name=AvailableRoom.CHATS.value
        ).send_chat_message(chat_id=chat_id, prepared_message=bot_message_serialized)

    except Exception as e:
        logger.error(e)
