from backend.enums import IntEnumM, EnumM


class SocketEventType(IntEnumM):
    # 0-99 посылает клиент
    LEAVE_TOPIC = 0
    JOIN_TOPIC = 1

    NEW_MESSAGE_TO_CHAT = 2
    READ_MESSAGE_IN_CHAT = 3
    NEW_COMMENT_TO_VACANCY = 4

    SELECT_CHAT_BOT_INTENT = 5

    LOCATION = 10

    MANAGER_LEAVE_CHAT = 30
    MANAGER_JOIN_CHAT = 31

    # 100-400 посылает сервер
    SERVER_SYSTEM_MESSAGE = 100

    SERVER_CHAT_MESSAGE_WAS_READ = 101

    SERVER_NEW_MESSAGE_IN_CHAT = 102  # group_send

    SERVER_CHAT_MESSAGE_UPDATED = 103
    SERVER_CHAT_UPDATED = 104
    SERVER_CHAT_LAST_MESSAGE_UPDATED = 105
    SERVER_CHAT_USER_STATUS_UPDATED = 106
    SERVER_CHAT_USER_JOINED = 107
    SERVER_CHAT_USER_LEAVED = 108
    SERVER_CHAT_STATE_UPDATED = 109

    SERVER_CHAT_BOT_INTENT_ACCEPTED = 110

    SERVER_COUNTERS_UPDATE = 120

    SERVER_APPEAL_STATUS_UPDATED = 121
    SERVER_APPEAL_JOB_STATUS_UPDATED = 122

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
    MESSAGES = 'messages'
    BOT = 'bot'
    VACANCIES = 'vacancies'
    APPEALS = 'appeals'
    DISTRIBUTORS = 'distributors'
    NOTIFICATIONS = 'notifications'
