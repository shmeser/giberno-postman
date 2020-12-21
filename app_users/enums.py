from enum import IntEnum, Enum


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


class LanguageProficiency(IntEnum):
    BEGINNER = 0
    ELEMENTARY = 1
    INTERMEDIATE = 2
    UPPER_INTERMEDIATE = 3
    ADVANCED = 4
    PROFICIENCY = 5

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_