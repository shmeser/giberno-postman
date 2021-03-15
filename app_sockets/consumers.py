import logging

from channels.generic.websocket import AsyncJsonWebsocketConsumer
from loguru import logger

from app_sockets.controllers import AsyncSocketController
from app_sockets.enums import SocketEventType
from app_sockets.mappers.request_models import SocketEventRM
from backend.errors.client_error import SocketError
from backend.errors.enums import SocketErrors
from backend.utils import chained_get


class GroupConsumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.socket_controller = None
        self.room_name = None
        self.room_id = None
        self.room_group_name = None

    async def connect(self):
        self.socket_controller = AsyncSocketController(self)
        self.user = self.scope["user"]

        self.room_id = chained_get(self.scope, 'url_route', 'kwargs', 'id')
        self.room_name = chained_get(self.scope, 'url_route', 'kwargs', 'room_name')

        self.room_group_name = f'{self.room_name}{self.room_id}' if self.room_id and self.room_name else None

        if self.user.is_authenticated:  # Проверка авторизации подключаемого соединения TODO проверка других разрешений
            # Добавляем соединение в группу
            await self.channel_layer.group_add(self.room_group_name, self.channel_name)
            await self.accept()  # Принимаем соединение
        else:
            # Принимаем соединение и сразу закрываем, чтобы не было ERR_CONNECTION_REFUSED
            await self.accept()
            await self.close(code=SocketErrors.NOT_AUTHORIZED.value)  # Закрываем соединение с кодом НЕАВТОРИЗОВАН

    async def receive_json(self, content, **kwargs):

        logger.debug(content)

        await self.channel_layer.group_send(self.room_group_name, {
            'type': 'system_message',
            'text': 'text'
        })
        # socket_event = SocketEventRM(content)

        # if socket_event.event_type == SocketEventType.LEAVE_GROUP:
        #     await self.leave_group(socket_event)
        #     return
        #
        # if socket_event.event_type == SocketEventType.REGISTER_PROFILE:
        #     await self.register_profiles(socket_event)

    # # Системное - предупреждение, информация
    async def system_message(self, data):
        await self.send_json(
            {
                'text': data['text'],
            },
        )

    async def disconnect(self, code):
        try:
            # Удаляем из группы
            await self.channel_layer.group_discard(self.room_group_name, self.channel_name)
            # await self.socket_controller.disconnect()
        except SocketError as error:
            await self.socket_controller.send_system_message(error.code, error.message)
        except Exception as e:
            print("DISCONNECT_ERROR", e)


class Consumer(AsyncJsonWebsocketConsumer):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = None
        self.socket_controller = None
        self.logger = logging.getLogger(__name__)

    async def connect(self):
        self.socket_controller = AsyncSocketController(self)
        self.user = self.scope["user"]

        # TODO запрещать создание дублирующего соединения

        if self.user.is_authenticated:  # Проверка авторизации подключаемого соединения
            await self.accept()  # Принимаем соединение
        else:
            # Принимаем соединение и сразу закрываем, чтобы не было ERR_CONNECTION_REFUSED
            await self.accept()
            await self.close(code=SocketErrors.NOT_AUTHORIZED.value)  # Закрываем соединение с кодом НЕАВТОРИЗОВАН

    async def receive_json(self, content, **kwargs):
        logger.debug(content)
        socket_event = SocketEventRM(content)

        if socket_event.event_type == SocketEventType.LEAVE_GROUP:
            await self.leave_group(socket_event)
            return

        if socket_event.event_type == SocketEventType.LOCATION:
            await self.update_location(socket_event)

    async def leave_group(self, event: SocketEventRM):
        try:
            self.user = await self.socket_controller.leave_group(event.token, event.group_name)
            # socket_print(self.user, event.event_type, event.group_name)
        except SocketError as error:
            await self.socket_controller.send_system_message(error.code, error.message)

    async def update_location(self, event: SocketEventRM):
        try:
            await self.channel_layer.send(self.channel_name, {
                'type': 'location_updated',
                'lat': 54,
                'lon': 34,
            })
            # self.user = await self.socket_controller.update_location(event)
            # socket_print(self.user, event.event_type, "%s, %s" % (event.lon, event.lat))
        except SocketError as error:
            await self.socket_controller.send_system_message(error.code, error.message)

    async def location_updated(self, event):
        await self.send_json(
            {
                'lat': 54,
                'lon': 34,
            },
        )

    async def system_message(self, system):
        await self.send_json(
            {
                'eventType': SocketEventType.SYSTEM_MESSAGE.value,
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
