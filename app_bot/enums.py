from enum import Enum


def choices(em):
    return [(e.value, e.name) for e in em]


class BotNotificationType(Enum):
    DEBUG = 'DEBUG'


class BotCommand(Enum):
    START = '/start'
    STOP = '/stop'

    ALL_ON = '/all_on'
    ALL_OFF = '/all_off'

    LOG_ERRORS_ON = '/log_errors_on'
    LOG_ERRORS_OFF = '/log_errors_off'
