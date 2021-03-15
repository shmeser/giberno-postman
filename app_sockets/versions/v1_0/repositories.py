import datetime

from channels.db import database_sync_to_async

from app_sockets.models import Socket
from app_users.models import UserProfile


class SocketsRepository:
    def __init__(self, user: UserProfile = None) -> None:
        super().__init__()
        self.user = user

    def add_socket(self, socket_id, room_name=None, room_id=None):
        Socket.objects.create(
            user=self.user,
            socket_id=socket_id,
            room_name=room_name,
            room_id=room_id
        )

    def clear(self):
        # Удаляет все сокеты при запуске сервера
        Socket.objects.all().delete()

    def remove_socket(self, socket_id):
        Socket.objects.filter(socket_id=socket_id).delete()

    def check_if_connected(self, room_name=None, room_id=None):
        return Socket.objects.filter(user=self.user, room_name=room_name, room_id=room_id).exists()

    def get_connected_groups_ids(self, group_type):
        return Socket.objects.filter(group_type=group_type).values_list('group_id', flat=True)

    def get_connected_profiles(self, group_type, group_id):
        connected = Socket.objects.filter(
            group_type=group_type, group_id=group_id).values_list('user_id', flat=True)
        if len(connected) == 0:
            return None
        return UserProfile.objects.filter(
            pk__in=connected,
            privatesettingsmodel__position=True)  # Отсекаем по приватности

    def clear_old_sockets(self):
        ts = datetime.datetime.now() - datetime.timedelta(hours=1)
        Socket.objects.filter(created_dt__lte=ts).delete()

    def get_sockets_from_chat(self, chat):
        return Socket.objects.filter(user__in=chat.users.all())

    def get_sockets_from_user(self, user):
        return Socket.objects.filter(user=user)

    def is_online_user(self):
        return Socket.objects.filter(user_id=self.user.id).exists()


class AsyncSocketsRepository(SocketsRepository):
    def __init__(self, user: UserProfile = None) -> None:
        super().__init__(user)

    @database_sync_to_async
    def add_socket(self, socket_id, room_name=None, room_id=None):
        return super().add_socket(socket_id, room_name, room_id)

    @database_sync_to_async
    def remove_socket(self, socket_id):
        super().remove_socket(socket_id)

    @database_sync_to_async
    def check_if_connected(self, room_name=None, room_id=None):
        return super().check_if_connected(room_name, room_id)

    @database_sync_to_async
    def get_connected_groups_ids(self, group_type):
        return super().get_connected_groups_ids(group_type)

    @database_sync_to_async
    def get_connected_profiles(self, group_type, group_id):
        return super().get_connected_profiles(group_type, group_id)

    @database_sync_to_async
    def get_sockets_from_chat(self, chat):
        return super().get_sockets_from_chat(chat)

    @database_sync_to_async
    def get_sockets_from_user(self, user):
        return super().get_sockets_from_user(user)
