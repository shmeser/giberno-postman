from enum import IntEnum, Enum


class RESTErrors(IntEnum):
    BAD_REQUEST = 400
    NOT_AUTHORIZED = 401
    FORBIDDEN = 403
    NOT_FOUND = 404
    CUSTOM_DETAILED_ERROR = 499
    INTERNAL_SERVER_ERROR = 500


class ErrorsCodes(Enum):
    SOCIAL_ALREADY_IN_USE = 'Данным способом уже зарегистрирован другой пользователь'


class SocketErrors(IntEnum):
    USER_NOT_FOUND = 1004
