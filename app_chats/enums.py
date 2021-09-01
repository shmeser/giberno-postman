from backend.enums import IntEnumM


class ChatMessageType(IntEnumM):
    SIMPLE = 1  # Обычное текстовое сообщение с возможностью прикрепления файлов
    INFO = 2  # Информационное сообщение с иконкой


class ChatMessageIconType(IntEnumM):
    DEFAULT = 0  # По умолчанию
    ALARM = 1  # Колокольчик
    CONGRATULATIONS = 2  # Поздравление
    WAITING = 3  # Ожидание
    SUPPORT = 4  # Поддержка


class ChatManagerState(IntEnumM):
    BOT_IS_USED = 0  # Общение с ботом
    NEED_MANAGER = 1  # Необходим менеджер для ответа
    MANAGER_CONNECTED = 2  # Менеджер подключен


class ChatMessageActionType(IntEnumM):
    BOT_INTENT = 0  # Бот просит выбрать тему
    DISTRIBUTOR_SHOPS = 1  # Магазины в торговой сети
    SHOP_VACANCIES = 2  # Вакансии магазина
    VACANCY = 3  # Вакансия
    APPEALS = 4  # Заявки
    SUPPORT = 5  # Поддержка
