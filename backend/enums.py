from enum import Enum, IntEnum


class IntEnumM(IntEnum):
    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def has_key(cls, key):
        return key in cls.__members__


class EnumM(Enum):
    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def has_key(cls, key):
        return key in cls.__members__


class Platform(EnumM):
    ANDROID = 'android'
    IOS = 'ios'


class Environment(EnumM):
    LOCAL = 'LOCAL'
    DEVELOP = 'DEVELOP'
    STAGE = 'STAGE'
    RELEASE = 'RELEASE'
