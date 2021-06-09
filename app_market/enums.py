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
    CANCELED = 2
    REJECTED = 3
    COMPLETED = 4


class ShiftAppealStatus(IntEnumM):
    INITIAL = 0
    CONFIRMED = 1
    CANCELED = 2
    REJECTED = 3
    COMPLETED = 4


class AppealCancelReason(IntEnumM):
    CUSTOM = 0  # Причина будет указана самостоятельно текстом
    MISTAKE = 1  # Заявка отменена, так как создана по ошибке
    ACCIDENT = 2  # Отмена из-за непредвиденных ситуаций


class ManagerAppealCancelReason(IntEnumM):
    CUSTOM = 0  # Причина будет указана самостоятельно текстом
    MISTAKE = 1  # Заявка принята была по ошибке
    ACCIDENT = 2  # Отмена из-за непредвиденных ситуаций
    NO_PASSPORT = 3  # Нет паспорта
    WRONG_PASSPORT = 4  # Паспортные данные не верны
    NO_INN = 5  # Нет ИНН
    NO_SNILS = 6  # Нет СНИЛС
    NO_MEDICAL_BOOK = 7  # Нет медкнижки
    NO_DRIVER_LICENCE = 8  # Нет водительского удостоверения


class SecurityPassRefuseReason(IntEnumM):
    CUSTOM = 0  # Причина будет указана самостоятельно текстом
    NO_PASSPORT = 3  # Нет паспорта
    MANAGER_SUPPORT_NEED = 9  # Требуется помощь менеджера


class FireByManagerReason(IntEnumM):
    CUSTOM = 0  # Причина будет указана самостоятельно текстом
    INCOMPETENT = 1  # Некомпетентен - не справляется с обязанностями
    DRUNK = 2  # В состоянии алкогольного/наркотического опьянения


class ShiftWorkTime(IntEnumM):
    # Тип времени смены (время начала)
    MORNING = 0  # Утренняя
    DAY = 1  # Дневная
    EVENING = 2  # Вечерняя


class JobStatusForClient(IntEnumM):
    NO_JOB = 0  # Работы нет
    JOB_NOT_SOON = 1  # Работа нескоро
    JOB_SOON = 2  # Работа скоро
    JOB_IN_PROCESS = 3  # Работа в процессе
    WAITING_FOR_COMPLETION = 4  # Ждет завершения
    COMPLETED = 5  # Завершена


class JobStatus(IntEnumM):
    JOB_SOON = 2  # Работа скоро
    JOB_IN_PROCESS = 3  # Работа в процессе
    WAITING_FOR_COMPLETION = 4  # Ждет завершения
    COMPLETED = 5  # Завершена
