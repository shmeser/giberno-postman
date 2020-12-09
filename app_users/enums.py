from enum import IntEnum


class Gender(IntEnum):
    FEMALE = 0
    MALE = 1


class Status(IntEnum):
    NEW = 0
    ACTIVE = 1
    BLOCKED = 2


class AccountType(IntEnum):
    ADMIN = 0
    MANAGER = 1
    SECURITY = 2
    SELF_EMPLOYED = 3

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_