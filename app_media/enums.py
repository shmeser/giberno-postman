from enum import IntEnum, Enum


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
    FLAG = 8


class FileDownloadStatus(IntEnum):
    INITIAL = 0
    SAVED = 1
    NOT_EXIST = 2
    FAIL = 3


class MimeTypes(Enum):
    PDF = 'application/pdf'
    PNG = 'image/png'
    SVG = 'image/svg+xml'
