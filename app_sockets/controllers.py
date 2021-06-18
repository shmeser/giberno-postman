from asgiref.sync import async_to_sync
from channels.layers import get_channel_layer
from loguru import logger

from app_sockets.enums import AvailableRoom, AvailableVersion
from app_sockets.mappers import RoutingMapper
from app_users.enums import NotificationAction, NotificationType
from app_users.models import UserProfile
from backend.controllers import PushController
from backend.utils import chained_get, datetime_to_timestamp


class SocketController:
    def __init__(self, me: UserProfile = None, version=None, room_name=None) -> None:
        super().__init__()
        self.me = me
        self.version = version
        self.room_name = room_name
        self.own_repository_class = RoutingMapper.room_repository(version)
        self.repository_class = RoutingMapper.room_repository(version, room_name)

    def send_notification_to_one_connection(self, socket_id, prepared_data):
        # Отправка уведомления в одиночный канал подключенного пользователя
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.send)(socket_id, {
            'type': 'notification_handler',
            'prepared_data': prepared_data
        })

    def send_notification_to_many_connections(self, sockets, prepared_data):
        channel_layer = get_channel_layer()
        for socket in sockets:
            async_to_sync(channel_layer.send)(socket, {
                'type': 'notification_handler',
                'prepared_data': prepared_data
            })

    def send_notification_to_my_connection(self, prepared_data):
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

    @staticmethod
    def send_message_to_connections_group(group_name, data):
        # Отправка сообщения в групповой канал
        channel_layer = get_channel_layer()
        async_to_sync(channel_layer.group_send)(group_name, data)

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

    def send_message_to_many_connections(self, sockets, data):
        channel_layer = get_channel_layer()
        if sockets:
            for socket in sockets:
                async_to_sync(channel_layer.send)(socket, data)

    def send_chat_message(self, prepared_message=None, chat_id=None):
        try:

            group_name = f'{AvailableRoom.CHATS.value}{chat_id}'
            # Отправялем сообщение в канал по сокетам
            self.send_message_to_connections_group(group_name, {
                'type': 'chat_message',
                'chat_id': chat_id,
                'prepared_data': prepared_message,
            })

            personalized_chat_variants_with_sockets, chat_users, push_title, inactive_mng_ids = self.repository_class(
                me=self.me
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
                                'state': chained_get(data, 'chat', 'state'),
                                'firstUnreadMessage': chained_get(data, 'chat', 'firstUnreadMessage'),
                                'lastMessage': prepared_message,
                                'blockedAt': chained_get(data, 'chat', 'blockedAt'),
                            },
                            'indicators': {
                                'chatsUnreadMessages': chained_get(data, 'chats_unread_messages'),
                            }
                        }
                    )

            # Отправляем сообщение по пушам всем участникам чата
            PushController().send_message(
                users_to_send=chat_users.exclude(id__in=inactive_mng_ids),  # Не отправляем пуши неактивным менеджерам
                title=push_title,
                message=chained_get(prepared_message, 'text', default=''),
                uuid=chained_get(prepared_message, 'uuid', default=''),
                action=NotificationAction.CHAT.value,
                subject_id=chat_id,
                notification_type=NotificationType.CHAT.value,
                icon_type=''
            )

        except Exception as e:
            logger.error(e)

    def send_chat_state(self, state=None, chat_id=None, active_managers_ids=[]):
        try:
            chat_repository = RoutingMapper.room_repository(
                version=AvailableVersion.V1_0.value, room_name=AvailableRoom.CHATS.value
            )
            managers, relevant_managers_sockets, blocked_at = chat_repository().get_managers_and_sockets(
                chat_id=chat_id
            )
            for socket in relevant_managers_sockets:
                self.send_message_to_one_connection(
                    socket,
                    {
                        'type': 'chat_state_updated',
                        'prepared_data': {
                            'id': chat_id,
                            'state': state,
                            'activeManagersIds': active_managers_ids,
                            'blockedAt': datetime_to_timestamp(blocked_at) if blocked_at is not None else None
                        }
                    }
                )

        except Exception as e:
            logger.error(e)
