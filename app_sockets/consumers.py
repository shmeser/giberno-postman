from channels.generic.websocket import AsyncJsonWebsocketConsumer
from loguru import logger

from app_sockets.async_controllers import AsyncSocketController
from app_sockets.enums import SocketEventType
from backend.errors.enums import SocketErrors
from backend.errors.ws_exceptions import WebSocketError
from backend.utils import chained_get


class Consumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.socket_controller = None
        self.version = None
        self.user = None
        self.room_name = None
        self.room_id = None
        self.group_name = None
        self.is_group_consumer = False

    async def connect(self):
        self.version = chained_get(self.scope, 'url_route', 'kwargs', 'version')
        self.user = chained_get(self.scope, 'user')
        self.socket_controller = AsyncSocketController(self)
        try:
            await self.accept()  # Принимаем соединение

            if self.user.is_authenticated:  # Проверка авторизации подключаемого соединения
                await self.socket_controller.store_single_connection()
                await self.socket_controller.send_counters()
            else:
                # После установления сразу закрываем содинение, чтобы не было ERR_CONNECTION_REFUSED
                await self.close(code=SocketErrors.NOT_AUTHORIZED.value)  # Закрываем соединение с кодом НЕАВТОРИЗОВАН
        except Exception as e:
            logger.error(e)
            await self.close(code=SocketErrors.BAD_REQUEST.value)  # Закрываем соединение с кодом BAD REQUEST

    async def disconnect(self, code):
        try:
            if self.user.is_authenticated:
                await self.socket_controller.remove_connection()
        except Exception as e:
            logger.error(e)

    async def receive_json(self, content, **kwargs):
        logger.info(content)

        handler_type = 'server_message_handler'
        data = content

        try:
            if content.get('eventType') == SocketEventType.LEAVE_TOPIC.value:
                await self.socket_controller.leave_topic(content)
            elif content.get('eventType') == SocketEventType.JOIN_TOPIC.value:
                await self.socket_controller.join_topic(content)
            elif content.get('eventType') == SocketEventType.LOCATION.value:
                await self.socket_controller.update_location(content)
            elif content.get('eventType') == SocketEventType.NEW_MESSAGE_TO_CHAT.value:
                await self.socket_controller.client_message_to_chat_async(content)
            elif content.get('eventType') == SocketEventType.READ_MESSAGE_IN_CHAT.value:
                await self.socket_controller.client_read_message_in_chat(content)
            elif content.get('eventType') == SocketEventType.MANAGER_LEAVE_CHAT.value:
                await self.socket_controller.manager_leave_chat(content)
            elif content.get('eventType') == SocketEventType.MANAGER_JOIN_CHAT.value:
                await self.socket_controller.manager_join_chat(content)
            else:
                await self.channel_layer.send(self.channel_name, {
                    'type': handler_type,
                    'prepared_data': data
                })
        except WebSocketError as error:
            await self.channel_layer.send(self.channel_name, {
                'type': 'error_handler',
                'code': error.code,
                'details': error.details,
            })

    # Общий обработчик серверных сообщений
    async def server_message_handler(self, data):
        logger.info({
            'eventType': data.get('event_type', SocketEventType.SERVER_SYSTEM_MESSAGE.value),
            **data.get('prepared_data')
        })
        await self.send_json(
            {
                'eventType': data.get('event_type', SocketEventType.SERVER_SYSTEM_MESSAGE.value),
                **data.get('prepared_data')
            },
        )

    # Уведомление
    async def notification_handler(self, data):
        logger.info({
            'eventType': SocketEventType.NOTIFICATION.value,
            'notification': data.get('prepared_data'),
        })
        await self.send_json(
            {
                'eventType': SocketEventType.NOTIFICATION.value,
                'notification': data.get('prepared_data'),
            },
        )

    # Сообщение об ошибке с кодом и деталями
    async def error_handler(self, data):
        logger.info({
            'eventType': SocketEventType.ERROR.value,
            'error': {
                'code': data.get('code'),
                'details': data.get('details')
            }
        })
        await self.send_json(
            {
                'eventType': SocketEventType.ERROR.value,
                'error': {
                    'code': data.get('code'),
                    'details': data.get('details')
                }
            },
        )

    """ Остальные обработчики """

    # Сообщения в чате
    async def chat_message(self, data):
        logger.info({
            'eventType': SocketEventType.SERVER_NEW_MESSAGE_IN_CHAT.value,
            'chat': {
                'id': data.get('chat_id')
            },
            'message': data.get('prepared_data')
        })
        await self.send_json(
            {
                'eventType': SocketEventType.SERVER_NEW_MESSAGE_IN_CHAT.value,
                'chat': {
                    'id': data.get('chat_id')
                },
                'message': data.get('prepared_data')
            },
        )

    # Сообщение в чате обновлено
    async def chat_message_updated(self, data):
        logger.info({
            'eventType': SocketEventType.SERVER_CHAT_MESSAGE_UPDATED.value,
            'chat': {
                'id': data.get('chat_id')
            },
            'message': data.get('prepared_data')
        })
        await self.send_json(
            {
                'eventType': SocketEventType.SERVER_CHAT_MESSAGE_UPDATED.value,
                'chat': {
                    'id': data.get('chat_id')
                },
                'message': data.get('prepared_data')
            },
        )

    # Последнее сообщение в чате обновлено
    async def chat_last_msg_updated(self, data):
        logger.info({
            'eventType': SocketEventType.SERVER_CHAT_LAST_MESSAGE_UPDATED.value,
            'chat': data.get('prepared_data'),
            'indicators': data.get('indicators')
        })
        await self.send_json(
            {
                'eventType': SocketEventType.SERVER_CHAT_LAST_MESSAGE_UPDATED.value,
                'chat': data.get('prepared_data'),
                'indicators': data.get('indicators')
            },
        )

    # Сообщение чата прочитано
    async def chat_message_was_read(self, data):
        logger.info(
            {
                'eventType': SocketEventType.SERVER_CHAT_MESSAGE_WAS_READ.value,
                'chat': data.get('chat'),
                'message': data.get('message'),
                'indicators': data.get('indicators')
            }
        )
        await self.send_json(
            {
                'eventType': SocketEventType.SERVER_CHAT_MESSAGE_WAS_READ.value,
                'chat': data.get('chat'),
                'message': data.get('message'),
                'indicators': data.get('indicators')
            },
        )

    # Информация о чате
    async def chat_info(self, data):
        logger.info(
            {
                'eventType': SocketEventType.SERVER_CHAT_UPDATED.value,
                'chat': data.get('prepared_data')
            }
        )
        await self.send_json(
            {
                'eventType': SocketEventType.SERVER_CHAT_UPDATED.value,
                'chat': data.get('prepared_data')
            },
        )

    # Счетчики
    async def counters_for_indicators(self, data):
        logger.info({
            'eventType': SocketEventType.SERVER_COUNTERS_UPDATE.value,
            'indicators': data.get('prepared_data')
        })
        await self.send_json(
            {
                'eventType': SocketEventType.SERVER_COUNTERS_UPDATE.value,
                'indicators': data.get('prepared_data'),
                'userId': self.user.id
            },
        )

    # Состояние чата изменилось - менеджер подсоединился или завершил консультацию
    async def chat_state_updated(self, data):
        logger.info({
            'eventType': SocketEventType.SERVER_CHAT_STATE_UPDATED.value,
            'chat': data.get('prepared_data')
        })
        await self.send_json(
            {
                'eventType': SocketEventType.SERVER_CHAT_STATE_UPDATED.value,
                'chat': data.get('prepared_data')
            },
        )

    # Состояние чата изменилось - менеджер подсоединился или завершил консультацию
    async def appeal_status_updated(self, data):
        logger.info({
            'eventType': SocketEventType.SERVER_APPEAL_STATUS_UPDATED.value,
            'appeal': data.get('prepared_data')
        })
        await self.send_json(
            {
                'eventType': SocketEventType.SERVER_APPEAL_STATUS_UPDATED.value,
                'appeal': data.get('prepared_data')
            },
        )


class GroupConsumer(Consumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.is_group_consumer = True

    async def connect(self):

        self.socket_controller = AsyncSocketController(self)
        self.version = chained_get(self.scope, 'url_route', 'kwargs', 'version')
        self.user = chained_get(self.scope, 'user')

        try:
            self.room_id = chained_get(self.scope, 'url_route', 'kwargs', 'id')
            self.room_name = chained_get(self.scope, 'url_route', 'kwargs', 'room_name')

            self.group_name = f'{self.room_name}{self.room_id}' if self.room_id and self.room_name else None

            await self.accept()  # Принимаем соединение

            # Проверка авторизации подключаемого соединения, версии и различных разрешений
            if self.user.is_authenticated:
                if await self.socket_controller.check_permission_for_group_connection():
                    # Добавляем соединение в группу
                    await self.channel_layer.group_add(self.group_name, self.channel_name)
                    await self.socket_controller.store_group_connection()
            else:
                # Принимаем соединение и сразу закрываем, чтобы не было ERR_CONNECTION_REFUSED
                await self.close(code=SocketErrors.NOT_AUTHORIZED.value)  # Закрываем соединение с кодом UNAUTHORIZED
        except Exception as e:
            logger.error(e)
            await self.close(code=SocketErrors.BAD_REQUEST.value)  # Закрываем соединение с кодом BAD REQUEST

    async def disconnect(self, code):
        try:
            # Удаляем из группы
            await self.channel_layer.group_discard(self.group_name, self.channel_name)
            await self.socket_controller.remove_connection()
        except Exception as e:
            logger.error(e)

    async def receive_json(self, content, **kwargs):
        logger.debug(content)

        handler_type = 'server_message_handler'
        data = content

        try:
            if content.get('eventType') == SocketEventType.NEW_MESSAGE_TO_CHAT.value:
                await self.socket_controller.client_message_to_chat(content)
            # elif content.get('eventType') == SocketEventType.NEW_COMMENT_TO_VACANCY.value:
            #     pass
            # elif content.get('eventType') == SocketEventType.READ_MESSAGE_IN_CHAT.value:
            #     pass
            else:
                await self.channel_layer.group_send(self.group_name, {
                    'type': handler_type,
                    'prepared_data': data
                })
        except WebSocketError as error:
            await self.channel_layer.send(self.channel_name, {
                'type': 'error_handler',
                'code': error.code,
                'details': error.details,
            })
