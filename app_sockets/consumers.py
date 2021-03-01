import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer

from app_sockets.controllers import AsyncSocketController
from app_sockets.enums import SocketEventType
from app_sockets.mappers.request_models import SocketEventRM
from backend.errors.client_error import SocketError


class Consumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.socket_controller = None
        self.room_name = None
        self.room_id = None
        self.room_group_name = None
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        self.socket_controller = AsyncSocketController(self)
        self.user = self.scope["user"]

        self.room_id = self.scope['url_route']['kwargs']['id']
        self.room_name = self.scope['url_route']['kwargs']['room_name']

        self.room_group_name = f'{self.room_name}_{self.room_id}'

        if self.user.is_authenticated:  # also you can add more restrictions here
            await self.accept()
        else:
            await self.close()

    async def receive_json(self, content, **kwargs):
        socket_event = SocketEventRM(content)

        if socket_event.event_type == SocketEventType.LEAVE_GROUP:
            await self.leave_group(socket_event)
            return

        if socket_event.event_type == SocketEventType.LOCATION:
            await self.update_location(socket_event)
            return

        if socket_event.event_type == SocketEventType.REGISTER_PROFILE:
            await self.register_profiles(socket_event)

    async def leave_group(self, event: SocketEventRM):
        try:
            self.user = await self.socket_controller.leave_group(event.token, event.group_name)
            # socket_print(self.user, event.event_type, event.group_name)
        except SocketError as error:
            await self.socket_controller.send_system_message(error.code, error.message)

    async def update_location(self, event: SocketEventRM):
        try:
            self.user = await self.socket_controller.update_location(event.token, event.lon, event.lat)
            # socket_print(self.user, event.event_type, "%s, %s" % (event.lon, event.lat))
        except SocketError as error:
            await self.socket_controller.send_system_message(error.code, error.message)

    async def register_profiles(self, event: SocketEventRM):
        try:
            self.user = await self.socket_controller.register_profiles(event.token, event.profile_id)
            # socket_print(self.user, event.event_type, event.profile_id)
        except SocketError as error:
            await self.socket_controller.send_system_message(error.code, error.message)

    """ type = event_message хендлер для типа серверных сообщений"""

    async def server_event(self, event):
        # socket_print(self.user, event.get('eventType'), event.get('data'))
        await self.send_json(
            {
                'data': event.get('data'),
                'eventType': event.get('eventType')
            }
        )

    async def notification_message(self, notification):
        await self.send_json(
            {
                'id': notification.get('id'),
                'receiver': notification.get('receiver'),
                'created': notification.get('created'),
                'data': notification.get('data'),
                'uuid': notification.get('uuid'),
                'title': notification.get('title'),
                'body': notification.get('body'),
                'notificationType': notification.get('notification_type'),
                'eventType': SocketEventType.NOTIFICATION,
            },
        )

    # Системное - предупреждение, информация
    async def system_message(self, system):
        await self.send_json(
            {
                'eventType': SocketEventType.SYSTEM_MESSAGE,
                'message': system['message'],
            },
        )

    async def disconnect(self, code):
        try:
            await self.socket_controller.disconnect()
        except SocketError as error:
            await self.socket_controller.send_system_message(error.code, error.message)
        except Exception as e:
            print("DISCONNECT_ERROR", e)
