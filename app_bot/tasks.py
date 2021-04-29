import uuid

from loguru import logger

from app_bot.enums import ChatterBotIntentCode
from app_chats.enums import ChatMessageType, ChatManagerState
from app_sockets.controllers import SocketController
from app_sockets.enums import AvailableRoom, AvailableVersion
from app_sockets.mappers import RoutingMapper
from app_users.enums import AccountType, NotificationAction, NotificationType, NotificationIcon
from backend.controllers import PushController
from giberno.celery import app


@app.task
def delayed_checking_for_bot_reply(version, chat_id, user_id, message_text):
    try:
        user_repository = RoutingMapper.room_repository(
            version=version, room_name=AvailableRoom.USERS.value)
        user = user_repository().get_by_id(user_id)
        # Проверяем необходимость отправки сообщения в чат от имени бота
        if user is None or user.account_type != AccountType.SELF_EMPLOYED.value:
            return

        chat_repository = RoutingMapper.room_repository(
            version=version, room_name=AvailableRoom.CHATS.value)
        chat = chat_repository().get_by_id(chat_id)
        if chat.deleted is False or chat.state != ChatManagerState.BOT_IS_USED.value:
            return  # НЕ обрабатываем сообщения в удаленных чатах и в состоянии НЕ в BOT_IS_USED

        bot_repository = RoutingMapper.room_repository(
            version=version, room_name=AvailableRoom.BOT.value)
        message_repository = RoutingMapper.room_repository(
            version=version, room_name=AvailableRoom.MESSAGES.value)

        # TODO Определить тип ответа - список документов, форма, обычное сообщение и т.д.

        text_reply, intent_code = bot_repository.get_response(message_text)

        # Если запрошен менеджер в чат
        if intent_code == ChatterBotIntentCode.DISABLE.value:
            # переводим чат в состояние NEED_MANAGER
            chat.state = ChatManagerState.NEED_MANAGER.value
            # Добавляем всех релевантных менеджеров в чат
            managers = chat_repository().get_managers(chat_id)
            chat.users.add(*managers)  # добавляем в m2m несколько менеджеров с десериализацией через *

            chat.save()

            # Отправляем всем релевантным менеджерам по сокетам смену состояния чата
            managers_sockets = chat_repository().get_managers_sockets(chat_id)
            for socket_id in managers_sockets:
                # Отправялем сообщение автору сообщения о том, что оно прочитано
                SocketController(version=AvailableVersion.V1_0.value).send_message_to_one_connection(socket_id, {
                    'type': 'chat_state_updated',
                    'prepared_data': {
                        'id': chat_id,
                        'state': ChatManagerState.NEED_MANAGER.value,
                        'activeManagerId': None
                    },
                })

            # Отправляем всем релевантным менеджерам пуш о том что нужна помощь человека
            # uuid для массовой рассылки оповещений,
            # у пользователей в бд будут созданы оповещения с одинаковым uuid
            # uuid необходим на клиенте для фильтрации одинаковых данных, полученных по 2 каналам - сокеты и пуши
            common_uuid = uuid.uuid4()
            title = 'Необходима поддержка от менеджера'
            message = f'Пользователь {chat.subject_user.first_name} {chat.subject_user.last_name}'
            notification_type = NotificationType.SYSTEM.value
            action = NotificationAction.CHAT.value
            icon_type = NotificationIcon.DEFAULT.value
            PushController().send_notification(
                users_to_send=managers,
                title=title,
                message=message,
                common_uuid=common_uuid,
                action=action,
                subject_id=chat_id,
                notification_type=notification_type,
                icon_type=icon_type,
            )

        bot_message_serialized = message_repository(chat_id=chat_id).save_bot_message(
            {
                'message_type': ChatMessageType.SIMPLE.value,
                'text': text_reply
            }
        )

        SocketController(
            version=AvailableVersion.V1_0.value,
            room_name=AvailableRoom.CHATS.value
        ).send_chat_message(chat_id=chat_id, prepared_message=bot_message_serialized)

    except Exception as e:
        logger.error(e)
