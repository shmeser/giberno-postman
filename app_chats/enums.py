from backend.enums import IntEnumM


class ChatMessageType(IntEnumM):
    COMMAND = 0  # Нет в списке сообщений, отправляет клиент по REST/WS (сохраняются статистические данные в JSON поле)
    SIMPLE = 1  # Обычное текстовое сообщение с возможностью прикрепления файлов
    INFO = 2  # Информационное сообщение с иконкой
    NOTIFICATION = 3  # Сообщение по типу уведомления с иконками
    FORM = 4  # Приходит с сервера (необходимо подтверждение сообщением COMMAND)


class FormMessageStatus(IntEnumM):
    INITIAL = 0
    WORKER_CONFIRMED = 1  # Работник подтвердил
    EMPLOYER_CONFIRMED = 2  # Работодатель подтвердил
