from channels.db import database_sync_to_async
from django.contrib.postgres.aggregates import ArrayAgg

from app_sockets.models import Socket
from app_users.models import UserProfile


class SocketsRepository:
    def __init__(self, me: UserProfile = None) -> None:
        super().__init__()
        self.me = me

    def add_socket(self, socket_id, room_name=None, room_id=None):
        Socket.objects.create(
            user=self.me,
            socket_id=socket_id,
            room_name=room_name,
            room_id=room_id
        )

    def remove_socket(self, socket_id):
        Socket.objects.filter(user=self.me, socket_id=socket_id).delete()

    def check_if_connected(self, room_name=None, room_id=None):
        return Socket.objects.filter(user=self.me, room_name=room_name, room_id=room_id).exists()

    def get_user_connections(self):
        return Socket.objects.filter(user=self.me)


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
    def get_connections_for_users(self, users, room_name=None, room_id=None):
        return Socket.objects.filter(
            user__in=users,
            room_name=room_name,
            room_id=room_id
        ).aggregate(
            connections=ArrayAgg('socket_id')
        )['connections']
