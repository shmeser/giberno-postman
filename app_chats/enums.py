from backend.enums import IntEnumM


class ChatMessageType(IntEnumM):
    SIMPLE = 1  # Обычное текстовое сообщение с возможностью прикрепления файлов
    INFO = 2  # Информационное сообщение с иконкой


class ChatManagerState(IntEnumM):
    BOT_IS_USED = 0  # Общение с ботом
    NEED_MANAGER = 1  # Необходим менеджер для ответа
    MANAGER_CONNECTED = 2  # Менеджер подключен
