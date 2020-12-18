from enum import IntEnum


class MediaFormat(IntEnum):
    UNKNOWN = 0
    DOCUMENT = 1
    IMAGE = 2
    VIDEO = 3
    AUDIO = 4


class MediaType(IntEnum):
    OTHER = 0
    AVATAR = 1
    PASSPORT = 2
    INN = 3
    SNILS = 4
    MEDICAL_BOOK = 5
    DRIVER_LICENCE = 6
    LOGO = 7
