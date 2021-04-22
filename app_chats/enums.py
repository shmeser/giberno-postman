from backend.enums import IntEnumM


class ChatMessageType(IntEnumM):
    SIMPLE = 1  # Обычное текстовое сообщение с возможностью прикрепления файлов
    INFO = 2  # Информационное сообщение с иконкой
