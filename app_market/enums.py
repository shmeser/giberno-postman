from backend.enums import IntEnumM


class Currency(IntEnumM):
    BONUS = 0
    USD = 1
    EUR = 2
    RUB = 3


class TransactionType(IntEnumM):
    TEST = 0
    TRANSFER = 1  # Перевод
    DEPOSIT = 2  # Пополнение
    WITHDRAWAL = 3  # Вывод
    RETURN = 4  # Возврат


class TransactionStatus(IntEnumM):
    CREATED = 0  # Создана
    HOLD = 1  # Средства захолдированны
    CANCELED = 2  # Отменена (отмена холдирования)
    FAILED = 3  # Ошибка выполнения (недостаточно средств или сбой)
    COMPLETED = 4  # Успешно завершена


class VacancyEmployment(IntEnumM):
    PARTIAL = 0  # Частичная занятость
    FULL = 1  # Полная занятость


class WorkExperience(IntEnumM):
    NO = 0  # Без опыта - Начало пути
    INVALID = 1  # С ограниченными возможностями
    UNDERAGE = 2  # До 18 лет - несовершеннолетний
    MIDDLE = 3  # 1-3 года опыта
    STRONG = 4  # более 3 лет опыта


class ShiftStatus(IntEnumM):
    INITIAL = 0
    STARTED = 1
    COMPLETED = 2
