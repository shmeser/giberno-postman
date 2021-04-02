from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from loguru import logger

from app_chats.versions.v1_0.repositories import AsyncChatsRepository, AsyncMessagesRepository
from app_sockets.enums import SocketEventType, AvailableRoom
from app_sockets.mappers import RoutingMapper
from app_sockets.versions.v1_0.repositories import AsyncSocketsRepository, SocketsRepository
from app_users.enums import NotificationAction, NotificationType
from app_users.models import UserProfile
from app_users.versions.v1_0.repositories import AsyncProfileRepository
from backend.controllers import AsyncPushController
from backend.errors.enums import SocketErrors
from backend.errors.exceptions import EntityDoesNotExistException
from backend.errors.ws_exceptions import WebSocketError
from backend.utils import chained_get


class AsyncSocketController:
    def __init__(self, consumer=None) -> None:
        super().__init__()
        self.consumer = consumer

    async def store_single_connection(self):
        try:
            me = self.consumer.scope['user']  # Прользователь текущего соединения

            await AsyncSocketsRepository(me).add_socket(
                self.consumer.channel_name  # ид соединения
            )
        except Exception as e:
            logger.error(e)

    async def store_group_connection(self, **kwargs):
        try:
            me = self.consumer.scope['user']  # Прользователь текущего соединения

            await AsyncSocketsRepository(me).add_socket(
                self.consumer.channel_name,  # ид соединения,
                chained_get(kwargs, 'room_name', default=self.consumer.room_name),  # имя комнаты
                chained_get(kwargs, 'room_id', default=self.consumer.room_id)  # ид комнаты
            )

        except Exception as e:
            logger.error(e)

    async def remove_connection(self):
        me = self.consumer.scope['user']  # Пользователь текущего соединения
        await AsyncSocketsRepository(me).remove_socket(self.consumer.channel_name)

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
                code=SocketErrors.FORBIDDEN.value, details='Действие запрещено'
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

    async def check_if_connected(self):
        me = self.consumer.scope['user']  # Пользователь текущего соединения
        return await AsyncSocketsRepository(me).check_if_connected()

    async def check_permission_for_group_connection(self, **kwargs):
        try:
            # Проверка возможности присоединиться к определенному каналу в чате
            version = self.consumer.version
            room_name = chained_get(kwargs, 'room_name', default=self.consumer.room_name)
            room_id = chained_get(kwargs, 'room_id', default=self.consumer.room_id)
            me = self.consumer.scope['user']  # Пользователь текущего соединения
            # TODO версионность для маппера и контроллеров
            if not RoutingMapper.check_room_version(room_name, version):
                logger.info(f'Такой точки соединения не существует для версии {version}')

                if self.consumer.is_group_consumer:
                    # Закрываем соединение, если это GroupConsumer
                    await self.consumer.close(code=SocketErrors.NOT_FOUND.value)

                return False

            repository_class = RoutingMapper.room_repository(version, room_name)

            if not await repository_class(me).check_connection_to_group(room_id):
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
        user = await AsyncProfileRepository(me=self.consumer.scope['user']).update_location(event)
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
                # Обрабатываем полученное от клиента сообщение
                processed_serialized_message = await AsyncMessagesRepository(
                    me=self.consumer.scope['user']
                ).save_client_message(
                    chat_id=room_id,
                    content=content,
                )
                processed_serialized_chat, chat_users = await AsyncChatsRepository(
                    me=self.consumer.scope['user']
                ).get_client_chat(
                    chat_id=room_id,
                )

                # Отправялем сообщение обратно в канал по сокетам
                await self.consumer.channel_layer.group_send(group_name, {
                    'type': 'chat_message',
                    'chat_id': room_id,
                    'prepared_data': processed_serialized_message,
                })

                chat_users_connections = await AsyncSocketsRepository.get_connections_for_users(chat_users)

                # Отправляем обновленные данные о чате всем участникам чата по сокетам
                for connection_name in chat_users_connections:
                    await self.consumer.channel_layer.send(connection_name, {
                        'type': 'chat_info',
                        'prepared_data': processed_serialized_chat,
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
                    code=SocketErrors.FORBIDDEN.value, details='Действие запрещено'
                )

        except Exception as e:
            logger.error(e)


class SocketController:
    def __init__(self, me: UserProfile = None) -> None:
        super().__init__()
        self.me = me

    def send_notification_to_one_connection(self, prepared_data):
        # Отправка уведомления в одиночный канал подключенного пользователя
        connections = SocketsRepository(self.me).get_user_connections(**{
            'room_id': None,
            'room_name': None,
        })

        for connection in connections:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(connection.socket_id, {
                'type': 'notification_handler',
                'prepared_data': prepared_data
            })

    @staticmethod
    def send_notification_to_connections_group(group_name, prepared_data):
        # Отправка уведомления в групповой канал
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'notification_handler',
            'prepared_data': prepared_data
        })
