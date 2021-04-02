from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from loguru import logger

from app_chats.versions.v1_0.repositories import AsyncChatsRepository, AsyncMessagesRepository
from app_sockets.versions.v1_0.mappers import RoutingMapper
from app_sockets.versions.v1_0.repositories import AsyncSocketsRepository, SocketsRepository
from app_users.enums import NotificationAction, NotificationType
from app_users.models import UserProfile
from app_users.versions.v1_0.repositories import AsyncProfileRepository
from backend.controllers import AsyncPushController
from backend.errors.enums import SocketErrors
from backend.errors.exceptions import EntityDoesNotExistException
from backend.errors.ws_exceptions import WebSocketError
from backend.utils import chained_get
from giberno.settings import DEBUG


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

    async def disconnect(self):
        me = self.consumer.scope['user']  # Прользователь текущего соединения
        await AsyncSocketsRepository(me).remove_socket(self.consumer.channel_name)

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
                raise WebSocketError(code=SocketErrors.BAD_REQUEST.value, details=SocketErrors.BAD_REQUEST.name)
            # return False

    async def update_location(self, event):
        user = await AsyncProfileRepository(me=self.consumer.scope['user']).update_location(event)
        return user

    async def client_message_to_chat(self, content):
        try:
            # Обрабатываем полученное от клиента сообщение
            processed_serialized_message = await AsyncMessagesRepository(
                me=self.consumer.scope['user']
            ).save_client_message(
                chat_id=self.consumer.room_id,
                content=content,
            )
            processed_serialized_chat, chat_users = await AsyncChatsRepository(
                me=self.consumer.scope['user']
            ).get_client_chat(
                chat_id=self.consumer.room_id,
            )

            # Отправялем сообщение обратно в канал по сокетам
            await self.consumer.channel_layer.group_send(self.consumer.group_name, {
                'type': 'chat_message',
                'prepared_data': processed_serialized_message,
            })

            chat_users_connections = await AsyncSocketsRepository.get_connections_for_users(chat_users)

            # TODO используется GroupConsumer, возможно нужен Consumer
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
                subject_id=self.consumer.room_id,
                notification_type=NotificationType.CHAT.value,
                icon_type=''
            )

        except Exception as e:
            logger.error(e)

    async def send_system_message(self, code, message):
        try:
            await self.consumer.channel_layer.send(self.consumer.channel_name, {
                'type': 'error_handler',
                'code': code,
                'details': message,
            })
        except Exception as e:
            if DEBUG is True:
                logger.error(e)


class SocketController:
    def __init__(self, me: UserProfile = None) -> None:
        super().__init__()
        self.me = me

    def send_single_notification(self, prepared_data):
        # Отправка уведомления в одиночный канал подключенного пользователя
        connection = SocketsRepository(self.me).get_user_single_connection()

        if connection:
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.send)(connection.socket_id, {
                'type': 'notification_handler',
                'prepared_data': prepared_data
            })

    @staticmethod
    def send_group_notification(group_name, prepared_data):
        # Отправка уведомления в групповой канал
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'notification_handler',
            'prepared_data': prepared_data
        })
