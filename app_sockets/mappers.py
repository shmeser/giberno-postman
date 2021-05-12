import re

from app_bot.versions.v1_0 import repositories as bot_1_0
from app_chats.versions.v1_0 import repositories as chats_1_0
from app_market.versions.v1_0 import repositories as market_1_0
from app_sockets.enums import AvailableRoom, AvailableVersion
from app_sockets.versions.v1_0 import repositories as socket_1_0
from app_users.versions.v1_0 import repositories as user_1_0
from backend.utils import chained_get


class SocketEventRM:
    def __init__(self, data):
        self.token = data.get('token', None)
        self.group_name = data.get('groupName', None)
        self.event_type = data.get('eventType', None)
        self.profile_id = data.get('profileId', None)
        self.lat = data.get('lat', None)
        self.lon = data.get('lon', None)
        self.uuid = data.get('uuid', None)
        self.id = data.get('id', None)
        self.receiver = data.get('receiver', None)

        self.chat_id = data.get('chatId', None)
        self.message = data.get('message', None)


class RoutingMapper:
    @staticmethod
    def room_async_repository(version, room_name=None):

        repos = {
            AvailableVersion.V1_0.value: {
                None: socket_1_0.AsyncSocketsRepository,
                AvailableRoom.CHATS.value: chats_1_0.AsyncChatsRepository,
                AvailableRoom.MESSAGES.value: chats_1_0.AsyncMessagesRepository,
                AvailableRoom.BOT.value: bot_1_0.AsyncChatterBotRepository,
                AvailableRoom.USERS.value: user_1_0.AsyncProfileRepository,
                AvailableRoom.SHOPS.value: market_1_0.AsyncShopsRepository,
                AvailableRoom.VACANCIES.value: market_1_0.AsyncVacanciesRepository,
                AvailableRoom.APPEALS.value: market_1_0.AsyncShiftAppealsRepository,
                AvailableRoom.DISTRIBUTORS.value: market_1_0.AsyncDistributorsRepository,
                AvailableRoom.NOTIFICATIONS.value: user_1_0.AsyncNotificationsRepository,
            }
        }
        return chained_get(repos, version, room_name)

    @staticmethod
    def room_repository(version, room_name=None):
        repos = {
            AvailableVersion.V1_0.value: {
                None: socket_1_0.SocketsRepository,
                AvailableRoom.CHATS.value: chats_1_0.ChatsRepository,
                AvailableRoom.MESSAGES.value: chats_1_0.MessagesRepository,
                AvailableRoom.BOT.value: bot_1_0.ChatterBotRepository,
                AvailableRoom.USERS.value: user_1_0.ProfileRepository,
                AvailableRoom.SHOPS.value: market_1_0.ShopsRepository,
                AvailableRoom.VACANCIES.value: market_1_0.VacanciesRepository,
                AvailableRoom.APPEALS.value: market_1_0.ShiftAppealsRepository,
                AvailableRoom.DISTRIBUTORS.value: market_1_0.DistributorsRepository,
                AvailableRoom.NOTIFICATIONS.value: user_1_0.NotificationsRepository,
            }
        }
        return chained_get(repos, version, room_name)

    @staticmethod
    def check_room_version(room_name, version):
        # v1.0
        if version == AvailableVersion.V1_0.value and room_name in [
            AvailableRoom.CHATS.value,
            AvailableRoom.USERS.value,
            AvailableRoom.SHOPS.value,
            AvailableRoom.VACANCIES.value,
            AvailableRoom.DISTRIBUTORS.value,
            AvailableRoom.NOTIFICATIONS.value,
        ]:
            return True

        # v1.1 TODO для тестов пока
        if version == AvailableVersion.V1_1.value and room_name in [
            AvailableRoom.CHATS.value,
        ]:
            return True

        return False

    @staticmethod
    def get_rooms_for_version(version):
        # v1.0
        if version == AvailableVersion.V1_0.value:
            return [
                AvailableRoom.CHATS.value,
                AvailableRoom.USERS.value,
                AvailableRoom.SHOPS.value,
                AvailableRoom.VACANCIES.value,
                AvailableRoom.DISTRIBUTORS.value,
                AvailableRoom.NOTIFICATIONS.value,
            ]

        # v1.1 TODO для тестов пока
        if version == AvailableVersion.V1_1.value:
            return [
                AvailableRoom.CHATS.value,
            ]

        return False

    @classmethod
    def get_room_and_id(cls, version, group_name=None):
        room_name = None
        room_id = None
        room_names = cls.get_rooms_for_version(version)
        if group_name and room_names:
            room_names_str = '|'.join(room_names)
            return tuple(re.findall(rf'{room_names_str}|\d+', group_name))
        return room_name, room_id
