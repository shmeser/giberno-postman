from backend.enums import IntEnumM, EnumM


class SocketEventType(IntEnumM):
    # 0-99 посылает клиент
    LEAVE_TOPIC = 0
    JOIN_TOPIC = 1

    NEW_MESSAGE_TO_CHAT = 2
    READ_MESSAGE_IN_CHAT = 3
    NEW_COMMENT_TO_VACANCY = 4

    LOCATION = 10

    # 100-400 посылает сервер
    SERVER_SYSTEM_MESSAGE = 100

    SERVER_PROFILE_UPDATED = 101

    SERVER_NEW_MESSAGE_IN_CHAT = 102
    SERVER_MESSAGE_IN_CHAT_UPDATED = 103
    SERVER_CHAT_UPDATED = 104

    NOTIFICATION = 200

    TOPIC_LEAVED = 300
    TOPIC_JOINED = 301

    ERROR = 400


class AvailableVersion(EnumM):
    V1_0 = '1.0'
    V1_1 = '1.1'


class AvailableRoom(EnumM):
    CHATS = 'chats'
    SHOPS = 'shops'
    USERS = 'users'
    VACANCIES = 'vacancies'
    DISTRIBUTORS = 'distributors'
