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
    PROFILE_NOT_FILLED = 'Профиль не заполнен'
    PHONE_IS_USED = 'Этот номер телефона уже занят'
    EMAIL_IS_USED = 'Этот email уже занят'

    VALIDATION_ERROR = 'Ошибка валидации'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_

    @classmethod
    def has_key(cls, key):
        return key in cls.__members__


class SocketErrors(IntEnum):
    USER_NOT_FOUND = 1004
