# from fcm_django.models import FCMDevice
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from djangorestframework_camel_case.util import camelize
from loguru import logger

from app_sockets.enums import SocketGroupPrefix, SocketEventType
from app_sockets.versions.v1_0.repositories import AsyncSocketsRepository
from app_users.models import UserProfile
from app_users.versions.v1_0.repositories import AsyncJwtRepository
from app_users.versions.v1_0.repositories import AsyncProfileRepository
from app_users.versions.v1_0.serializers import ProfileSerializer
from backend.errors.client_error import SocketError
from backend.errors.enums import SocketErrors
from backend.errors.exceptions import EntityDoesNotExistException
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

    @staticmethod
    async def send_profile(profile: UserProfile):
        channel_layer = get_channel_layer()
        await channel_layer.group_send(SocketGroupPrefix.PROFILE.value + str(profile.id), {
            'type': 'server_event',  # обязательное поле для определения хэндлера
            'eventType': SocketEventType.SERVER_PROFILE_UPDATED,
            'data': camelize(ProfileSerializer(profile).data)
        })

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

    @staticmethod
    def send_profile(profile: UserProfile):
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(SocketGroupPrefix.PROFILE.value + str(profile.id), {
            'type': 'server_event',
            'eventType': SocketEventType.SERVER_PROFILE_UPDATED,
            'data': camelize(ProfileSerializer(profile).data)
        })
