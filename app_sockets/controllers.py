# from fcm_django.models import FCMDevice
from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from djangorestframework_camel_case.util import camelize

from app_sockets.enums import SocketGroupPrefix, SocketEventType, SocketGroupType
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

    async def leave_group(self, token, group_name):
        try:
            me = await AsyncJwtRepository().get_user(token)
            await self.consumer.channel_layer.group_discard(
                str(group_name),
                self.consumer.channel_name
            )
            await self.consumer.send_json({
                "eventType": SocketEventType.SYSTEM_MESSAGE,
                "leave": str(group_name),
                "title": self.consumer.channel_name,
            })
            return me
        except EntityDoesNotExistException:
            raise SocketError(SocketErrors.NOT_FOUND.name, SocketErrors.NOT_FOUND)

    async def update_location(self, event):
        user = await AsyncProfileRepository(me=self.consumer.scope['user']).update_location(event)
        return user

    async def register_profiles(self, token, profile_id):
        try:
            me = await AsyncJwtRepository().get_user(token)
            await AsyncSocketsRepository(me).append_socket(
                self.consumer.channel_name,
                SocketGroupType.PROFILE.value,
                profile_id)

            profile = await AsyncProfileRepository.get_by_id(profile_id)
            await self.consumer.send_json({
                "eventType": SocketEventType.SYSTEM_MESSAGE,
                "join": SocketGroupPrefix.PROFILE.value + str(profile.id),
                "title": self.consumer.channel_name,
            })
            await self.consumer.channel_layer.group_add(
                SocketGroupPrefix.PROFILE.value + str(profile.id),
                self.consumer.channel_name
            )

            await self.send_profile(profile)

            return me
        except Exception as e:
            print(e)
        except EntityDoesNotExistException:
            raise SocketError(SocketErrors.NOT_FOUND, SocketErrors.NOT_FOUND.name)

    @staticmethod
    async def send_profile(profile: UserProfile):
        channel_layer = get_channel_layer()
        await channel_layer.group_send(SocketGroupPrefix.PROFILE.value + str(profile.id), {
            'type': 'server_event',  # обязательное поле для определения хэндлера
            'eventType': SocketEventType.SERVER_PROFILE_UPDATED,
            'data': camelize(ProfileSerializer(profile).data)
        })

    async def disconnect(self):
        await AsyncSocketsRepository(self.consumer.user).remove_socket(self.consumer.channel_name)

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
