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
    # Images
    JPEG = 'image/jpeg'
    PNG = 'image/png'
    BMP = 'image/bmp',
    GIF = 'image/gif',
    TIFF = 'image/tiff',
    SVG = 'image/svg+xml'

    # Video
    AVI = 'video/x-msvideo',
    MOV = 'video/quicktime',
    MP4 = 'video/mp4',
    MPG = 'video/mpeg'

    # Audio
    MP3 = 'audio/mpeg',
    WAV = 'audio/x-wav',

    # Documents
    PDF = 'application/pdf'
    DOC = 'application/msword',
    RTF = 'text/richtext',
    TXT = 'text/plain',
    XLS = 'application/vnd.ms-excel'
    # TODO XLS = 'application/excel', проверить
