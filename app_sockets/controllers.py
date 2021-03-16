# from fcm_django.models import FCMDevice
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from loguru import logger

from app_sockets.enums import SocketEventType
from app_sockets.versions.v1_0.repositories import AsyncSocketsRepository, SocketsRepository
from app_users.models import UserProfile
from app_users.versions.v1_0.repositories import AsyncProfileRepository
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

    async def store_group_connection(self):
        try:
            me = self.consumer.scope['user']  # Прользователь текущего соединения

            await AsyncSocketsRepository(me).add_socket(
                self.consumer.channel_name,  # ид соединения,
                self.consumer.room_name,  # имя комнаты
                self.consumer.room_id  # ид комнаты
            )

        except Exception as e:
            logger.error(e)

    async def disconnect(self):
        me = self.consumer.scope['user']  # Прользователь текущего соединения
        await AsyncSocketsRepository(me).remove_socket(self.consumer.channel_name)

    async def check_if_connected(self):
        me = self.consumer.scope['user']  # Прользователь текущего соединения
        return await AsyncSocketsRepository(me).check_if_connected()

    async def update_location(self, event):
        user = await AsyncProfileRepository(me=self.consumer.scope['user']).update_location(event)
        return user

    async def send_system_message(self, code, message):
        try:
            await self.consumer.channel_layer.send(self.consumer.channel_name, {
                'type': 'system_message',
                'code': code,
                'message': message,
            })
        except Exception as exc:
            if DEBUG is True:
                print('[SOCKET ERROR] chats.controllers.send_system_message():')
                print('[ERROR MESSAGE] ' + str(exc))


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
                'type': 'server_event',
                'eventType': SocketEventType.NOTIFICATION.value,
                'data': prepared_data
            })

    @staticmethod
    def send_group_notification(group_name, prepared_data):
        # Отправка уведомления в групповой канал
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(group_name, {
            'type': 'server_event',
            'eventType': SocketEventType.NOTIFICATION.value,
            'data': prepared_data
        })
