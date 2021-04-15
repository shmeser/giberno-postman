from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from loguru import logger

from app_sockets.enums import SocketEventType, AvailableRoom, AvailableVersion
from app_sockets.mappers import RoutingMapper
from app_users.enums import NotificationAction, NotificationType, AccountType
from app_users.models import UserProfile
from backend.controllers import AsyncPushController, PushController
from backend.errors.enums import SocketErrors
from backend.errors.exceptions import EntityDoesNotExistException
from backend.errors.ws_exceptions import WebSocketError
from backend.utils import chained_get


class AsyncSocketController:
    def __init__(self, consumer=None) -> None:
        super().__init__()
        self.consumer = consumer
        self.own_repository_class = RoutingMapper.room_async_repository(consumer.version)
        self.repository_class = RoutingMapper.room_async_repository(consumer.version, consumer.room_name)

    async def store_single_connection(self):
        try:
            me = self.consumer.scope['user']  # Прользователь текущего соединения

            await self.own_repository_class(me).add_socket(
                self.consumer.channel_name  # ид соединения
            )
        except Exception as e:
            logger.error(e)
            raise WebSocketError(code=SocketErrors.BAD_REQUEST.value, details=e)

    async def store_group_connection(self, **kwargs):
        try:
            me = self.consumer.scope['user']  # Прользователь текущего соединения

            await self.own_repository_class(me).add_socket(
                self.consumer.channel_name,  # ид соединения,
                chained_get(kwargs, 'room_name', default=self.consumer.room_name),  # имя комнаты
                chained_get(kwargs, 'room_id', default=self.consumer.room_id)  # ид комнаты
            )

        except Exception as e:
            logger.error(e)
            raise WebSocketError(code=SocketErrors.BAD_REQUEST.value, details=e)

    async def remove_connection(self):
        me = self.consumer.scope['user']  # Пользователь текущего соединения
        await self.own_repository_class(me).remove_socket(self.consumer.channel_name)

    async def send_error(self, code, details):
        await self.consumer.channel_layer.send(self.consumer.channel_name, {
            'type': 'error_handler',
            'code': code,
            'details': details,
        })

    async def leave_topic(self, content):
        group_name = content.get('topic')

        # Удаляем соединение из группы
        await self.consumer.channel_layer.group_discard(group_name, self.consumer.channel_name)
        await self.topic_leaved(group_name)

    async def join_topic(self, content):
        room_name = None
        room_id = None
        group_name = content.get('topic')
        if group_name:
            room_name, room_id = RoutingMapper.get_room_and_id(self.consumer.version, group_name)

        if await self.check_permission_for_group_connection(**{
            'room_name': room_name,
            'room_id': room_id,
        }):
            # Добавляем соединение в группу
            await self.consumer.channel_layer.group_add(group_name, self.consumer.channel_name)
            await self.topic_joined(group_name)
        else:
            await self.send_error(
                code=SocketErrors.FORBIDDEN.value, details=SocketErrors.FORBIDDEN.name
            )

    async def topic_joined(self, topic):
        await self.consumer.channel_layer.send(self.consumer.channel_name, {
            'type': 'server_message_handler',
            'event_type': SocketEventType.TOPIC_JOINED.value,
            'prepared_data': {
                'topic': topic
            },
        })

    async def topic_leaved(self, topic):
        await self.consumer.channel_layer.send(self.consumer.channel_name, {
            'type': 'server_message_handler',
            'event_type': SocketEventType.TOPIC_LEAVED.value,
            'prepared_data': {
                'topic': topic
            },
        })

    async def check_permission_for_group_connection(self, **kwargs):
        try:
            # Проверка возможности присоединиться к определенному каналу в чате
            version = self.consumer.version
            room_name = chained_get(kwargs, 'room_name', default=self.consumer.room_name)
            room_id = chained_get(kwargs, 'room_id', default=self.consumer.room_id)
            me = self.consumer.scope['user']  # Пользователь текущего соединения

            if not RoutingMapper.check_room_version(room_name, version):
                logger.info(f'Такой точки соединения не существует для версии {version}')

                if self.consumer.is_group_consumer:
                    # Закрываем соединение, если это GroupConsumer
                    await self.consumer.close(code=SocketErrors.NOT_FOUND.value)

                return False

            self.repository_class = RoutingMapper.room_async_repository(version, room_name)

            if not await self.repository_class(me).check_permission_for_action(room_id):
                logger.info(f'Действие запрещено')
                if self.consumer.is_group_consumer:
                    # Закрываем соединение, если это GroupConsumer
                    await self.consumer.close(code=SocketErrors.FORBIDDEN.value)
                return False
            return True

        except EntityDoesNotExistException:
            logger.info(f'Объект не найден')
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.NOT_FOUND.value)
            else:
                raise WebSocketError(code=SocketErrors.NOT_FOUND.value, details=SocketErrors.NOT_FOUND.name)
        except Exception as e:
            logger.error(e)
            if self.consumer.is_group_consumer:
                # Закрываем соединение, если это GroupConsumer
                await self.consumer.close(code=SocketErrors.BAD_REQUEST.value)
            else:
                raise WebSocketError(code=SocketErrors.BAD_REQUEST.value, details=e)

    async def update_location(self, event):
        self.repository_class = RoutingMapper.room_async_repository(self.consumer.version, AvailableRoom.USERS.value)
        user = await self.repository_class(me=self.consumer.scope['user']).update_location(event)
        return user

    async def client_message_to_chat(self, content):
        try:
            room_id = self.consumer.room_id
            group_name = self.consumer.group_name
            if not room_id:
                room_id = chained_get(content, 'chatId')
                group_name = f'{AvailableRoom.CHATS.value}{room_id}'

            if await self.check_permission_for_group_connection(**{
                'room_name': AvailableRoom.CHATS.value,
                'room_id': room_id
            }):
                self.repository_class, message_repository = RoutingMapper.room_async_repository(
                    self.consumer.version, AvailableRoom.CHATS.value
                )
                # Обрабатываем полученное от клиента сообщение
                processed_serialized_message = await message_repository(
                    me=self.consumer.scope['user'],
                    chat_id=room_id,
                ).save_client_message(
                    content=content
                )

                personalized_chat_variants_with_sockets, chat_users = await self.repository_class(
                    me=self.consumer.scope['user']
                ).get_chat_for_all_participants(  # 10
                    chat_id=room_id,
                )

                # Отправялем сообщение обратно в канал по сокетам
                await self.consumer.channel_layer.group_send(group_name, {
                    'type': 'chat_message',
                    'chat_id': room_id,
                    'prepared_data': processed_serialized_message,
                })

                # Отправляем обновленные данные о чате всем участникам чата по сокетам
                for data in personalized_chat_variants_with_sockets:
                    for connection_name in data['sockets']:
                        await self.consumer.channel_layer.send(connection_name, {
                            'type': 'chat_last_msg_updated',
                            'prepared_data': {
                                'id': room_id,
                                'unreadCount': chained_get(data, 'chat', 'unreadCount'),
                                'lastMessage': processed_serialized_message
                            },
                        })

                # Отправляем сообщение по пушам всем участникам чата
                await AsyncPushController().send_message(
                    users_to_send=chat_users,
                    title='',
                    message=chained_get(content, 'text', default=''),
                    action=NotificationAction.CHAT.value,
                    subject_id=room_id,
                    notification_type=NotificationType.CHAT.value,
                    icon_type=''
                )
            else:
                await self.send_error(
                    code=SocketErrors.FORBIDDEN.value, details=SocketErrors.FORBIDDEN.name
                )

        except Exception as e:
            logger.error(e)
            raise WebSocketError(code=SocketErrors.BAD_REQUEST.value, details=str(e))

    async def client_read_message_in_chat(self, content):
        try:
            room_id = self.consumer.room_id
            if not room_id:
                room_id = chained_get(content, 'chatId')

            if await self.check_permission_for_group_connection(**{
                'room_name': AvailableRoom.CHATS.value,
                'room_id': room_id
            }) is False:
                await self.send_error(
                    code=SocketErrors.FORBIDDEN.value, details=SocketErrors.FORBIDDEN.name
                )
                return

            self.repository_class = RoutingMapper.room_async_repository(
                self.consumer.version, AvailableRoom.CHATS.value
            )

            message_repository = RoutingMapper.room_async_repository(
                self.consumer.version, AvailableRoom.MESSAGES.value
            )

            # Обрабатываем полученные от клиента данные
            (
                owner_prepared_msg,
                owner,
                owner_sockets,
                should_response_owner,
                owner_unread_cnt,
                my_unread_cnt,
                my_first_unread_message_prepared
            ) = \
                await message_repository(
                    me=self.consumer.scope['user'],
                    chat_id=room_id,
                ).client_read_message(
                    content=content,
                )

            # Отправялем ответ на свой запрос с числом непрочитанных сообщений в чате
            if my_unread_cnt is not None:
                await self.consumer.channel_layer.send(self.consumer.channel_name, {
                    'type': 'chat_message_was_read',
                    'chat': {
                        'id': room_id,
                        'unreadCount': my_unread_cnt,
                        'firstUnreadMessage': my_first_unread_message_prepared,
                    },
                    'message': {
                        'uuid': chained_get(content, 'uuid'),
                    }
                })

            if owner and owner.id != self.consumer.scope['user'].id and should_response_owner:
                # Если автор прочитаного сообщения не тот, кто его читает, и сообщение ранее не читали
                for socket_id in owner_sockets:
                    # Отправялем сообщение автору сообщения о том, что оно прочитано
                    await self.consumer.channel_layer.send(socket_id, {
                        'type': 'chat_message_updated',
                        'chat_id': room_id,
                        'prepared_data': owner_prepared_msg,
                    })

                    # Если прочитанное сообщение последнее в чате, то отправляем автору SERVER_CHAT_LAST_MSG_UPDATED
                    if owner_unread_cnt is not None:
                        await self.consumer.channel_layer.send(socket_id, {
                            'type': 'chat_last_msg_updated',
                            'prepared_data': {
                                'id': room_id,
                                'unreadCount': owner_unread_cnt,
                                'lastMessage': owner_prepared_msg
                            },
                        })

        except Exception as e:
            logger.error(e)
            raise WebSocketError(code=SocketErrors.CUSTOM_DETAILED_ERROR.value, details=str(e))


class SocketController:
    def __init__(self, me: UserProfile = None, version=None, room_name=None) -> None:
        super().__init__()
        self.me = me
        self.version = version
        self.room_name = room_name
        self.own_repository_class = RoutingMapper.room_repository(version)
        self.repository_class = RoutingMapper.room_repository(version, room_name)

    def send_notification_to_one_connection(self, prepared_data):
        # Отправка уведомления в одиночный канал подключенного пользователя
        try:
            connections = self.own_repository_class(self.me).get_user_connections(**{
                'room_id': None,
                'room_name': None,
            })

            for connection in connections:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.send)(connection.socket_id, {
                    'type': 'notification_handler',
                    'prepared_data': prepared_data
                })
        except Exception as e:
            logger.error(e)

    @staticmethod
    def send_notification_to_connections_group(group_name, prepared_data):
        # Отправка уведомления в групповой канал
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'notification_handler',
            'prepared_data': prepared_data
        })

    def send_message_to_my_connections(self, data):
        # Отправка сообщения в себе по сокетам, если есть подключения
        try:
            connections = self.own_repository_class(self.me).get_user_connections(**{
                'room_id': None,
                'room_name': None,
            })

            for connection in connections:
                channel_layer = get_channel_layer()
                async_to_sync(channel_layer.send)(connection.socket_id, data)
        except Exception as e:
            logger.error(e)

    def send_message_to_one_connection(self, socket_id, data):
        # Отправка уведомления в одиночный канал подключенного пользователя
        try:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(socket_id, data)
        except Exception as e:
            logger.error(e)

    def send_chat_message(self, prepared_message=None, chat_id=None):
        try:
            personalized_chat_variants_with_sockets, chat_users = self.repository_class(
                me=self.me
            ).get_chat_for_all_participants(chat_id)

            # Отправляем обновленные данные о чате всем участникам чата по сокетам
            for data in personalized_chat_variants_with_sockets:
                for connection_name in data['sockets']:
                    SocketController(version=AvailableVersion.V1_0.value).send_message_to_one_connection(
                        connection_name,
                        {
                            'type': 'chat_last_msg_updated',
                            'prepared_data': {
                                'id': chat_id,
                                'unreadCount': chained_get(data, 'chat', 'unreadCount'),
                                'lastMessage': prepared_message
                            },
                        }
                    )

            # Отправляем сообщение по пушам всем участникам чата
            PushController().send_message(
                users_to_send=chat_users,
                title='',
                message=chained_get(prepared_message, 'text', default=''),
                action=NotificationAction.CHAT.value,
                subject_id=chat_id,
                notification_type=NotificationType.CHAT.value,
                icon_type=''
            )

        except Exception as e:
            logger.error(e)

    def check_and_send_bot_reply(self, prepared_message=None, chat_id=None):
        try:
            # Проверяем необходимость отправки сообщения в чат от имени бота
            if self.me is None or self.me.account_type != AccountType.SELF_EMPLOYED.value:
                return

            # TODO Определить тип ответа - список документов, форма, обычное сообщение и т.д.

            bot_repository = RoutingMapper.room_repository(
                version=AvailableVersion.V1_0.value, room_name=AvailableRoom.BOT.value)
            message_repository = RoutingMapper.room_repository(
                version=AvailableVersion.V1_0.value, room_name=AvailableRoom.MESSAGES.value)

            reply = bot_repository.get_response(chained_get(prepared_message, 'text'))

            bot_message_serialized = message_repository(chat_id=chat_id).save_bot_message(
                {
                    'message_type': 1,
                    'text': reply,
                    'command_data': None
                }
            )

            personalized_chat_variants_with_sockets, chat_users = self.repository_class(
            ).get_chat_for_all_participants(chat_id)

            # Отправляем обновленные данные о чате всем участникам чата по сокетам
            for data in personalized_chat_variants_with_sockets:
                for connection_name in data['sockets']:
                    self.send_message_to_one_connection(
                        connection_name,
                        {
                            'type': 'chat_last_msg_updated',
                            'prepared_data': {
                                'id': chat_id,
                                'unreadCount': chained_get(data, 'chat', 'unreadCount'),
                                'lastMessage': bot_message_serialized
                            },
                        }
                    )

            # Отправляем сообщение по пушам всем участникам чата
            PushController().send_message(
                users_to_send=chat_users,
                title='',
                message=chained_get(bot_message_serialized, 'text', default=''),
                action=NotificationAction.CHAT.value,
                subject_id=chat_id,
                notification_type=NotificationType.CHAT.value,
                icon_type=''
            )
        except Exception as e:
            logger.error(e)
