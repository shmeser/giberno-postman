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
    CANCEL = 0  # Отмена
    DISTRIBUTOR = 1  # Торговая сеть
    SHOP = 2  # Магазин
    VACANCY = 3  # Вакансия
    SHIFT = 4  # Смена
    APPEAL = 5  # Заявка
