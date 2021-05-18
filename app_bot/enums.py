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
    # Темы разговоров бота для текстовых сообщений пользователя
    DISABLE = 0  # Отключение бота, разговор только с менеджером
    GREETING = 1  # Приветствие
    FAREWELL = 2  # Прощание
    ANSWERS_POSITIVE = 3  # Положительные ответы на вопросы бота
    ANSWERS_NEGATIVE = 4  # Отрицательные ответы на вопросы бота
    COMPLY = 5  # Оставить жалобу
    SHOP_ADDRESS = 6  # Где находится магазин?
    VACANCY_REQUIREMENTS = 7  # Требования к вакансии
    APPEAL_CONFIRMATION = 8  # Когда мне подтвердят работу
    SHIFT_TIME = 9  # Когда начинается моя смена
    WHAT_TO_TAKE_WITH = 10  # Что мне нужно иметь при себе
    CANCEL_APPEAL = 11  # Отказаться от вакансии
    VACANCIES_VARIETY = 12  # Какие у вас есть вакансии
    VACANCY_RATES = 13  # Почему такие ставки


class ChatterBotStates(IntEnum):
    # Состояния бота для чата с пользователем
    IDLE = 0  # Бот в ожидании
    QUESTION_ASKED = 1  # Бот задал вопрос и ждет ответа
    IRRELEVANT_ANSWER_TO_QUESTION = 2  # Бот получил некорректный ответ на свой вопрос,
    # при получении корректного ответа перейдет в состояние 0, при некорректном отклчится и позовет менеджера
