from enum import Enum


def choices(em):
    return [(e.value, e.name) for e in em]


class TelegramBotMessageType(Enum):
    PRIVATE = 'message'
    CHANNEL = 'channel_post'


class TelegramBotNotificationType(Enum):
    DEBUG = 'DEBUG'


class TelegramBotCommand(Enum):
    START = '/start'
    STOP = '/stop'

    DEBUG_ON = '/debug_on'
    DEBUG_OFF = '/debug_off'

    ALL_ON = '/all_on'
    ALL_OFF = '/all_off'

    LOG_ERRORS_ON = '/log_errors_on'
    LOG_ERRORS_OFF = '/log_errors_off'

    @classmethod
    def has_value(cls, value):
        return value in cls._value2member_map_
