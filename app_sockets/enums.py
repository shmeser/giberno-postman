from backend.enums import IntEnumM, EnumM


class SocketGroupType(IntEnumM):
    PROFILE = 1


class SocketGroupPrefix(EnumM):
    PROFILE = 'profile_'


class SocketEventType(IntEnumM):
    LEAVE_GROUP = 0
    LOCATION = 1

    REGISTER_PROFILE = 2

    SYSTEM_MESSAGE = 100

    SERVER_PROFILE_UPDATED = 101

    NOTIFICATION = 200
