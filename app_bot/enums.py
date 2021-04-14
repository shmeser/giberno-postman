from enum import IntEnum

from backend.enums import EnumM


class TelegramBotMessageType(EnumM):
    PRIVATE = 'message'
    CHANNEL = 'channel_post'


class TelegramBotNotificationType(EnumM):
    DEBUG = 'DEBUG'


class TelegramBotCommand(EnumM):
    START = '/start'
    STOP = '/stop'

    DEBUG_ON = '/debug_on'
    DEBUG_OFF = '/debug_off'

    ALL_ON = '/all_on'
    ALL_OFF = '/all_off'

    LOG_ERRORS_ON = '/log_errors_on'
    LOG_ERRORS_OFF = '/log_errors_off'


class ChatterBotIntentCode(IntEnum):
    DISABLE = 0  # Отключение бота, разговор только с менеджером
    GREETING = 1  # Приветствие
    FAREWELL = 2  # Прощание
    VACANCY = 3  # Вопросы по вакансии
